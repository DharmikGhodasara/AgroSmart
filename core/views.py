from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from .forms import CropRecommendationForm, ContactMessageForm
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
import os
import io
import base64
# matplotlib is used elsewhere in analytics; import pyplot for ad-hoc chart
from matplotlib import pyplot as plt  # type: ignore
# Scrapers for Phase 3
from .scrapers.prices import get_crop_prices
from .scrapers.rainfall import get_rainfall
from .scrapers.schemes import get_schemes
# Analytics for Phase 4
from .analytics.charts import build_from_dataset
from django.http import HttpResponse
from .ml import train_model

def home(request):
    return render(request, 'pages/home.html')

def crop_suggestion(request):
    form = CropRecommendationForm(request.POST or None)

    model_path = os.path.join(settings.BASE_DIR, 'core', 'ml', 'crop_model.joblib')
    label_path = os.path.join(settings.BASE_DIR, 'core', 'ml', 'label_encoder.joblib')

    prediction = None
    recommended_crops = None
    model_loaded = os.path.exists(model_path) and os.path.exists(label_path)

    if request.method == 'POST' and form.is_valid():
        if not model_loaded:
            messages.error(request, 'Model not found. Please run the training script to generate the model.')
        else:
            try:
                import joblib  # type: ignore
            except Exception as exc:
                messages.error(request, f'Prediction dependencies missing: {exc}')
            else:
                try:
                    model = joblib.load(model_path)
                    label_encoder = joblib.load(label_path)

                    soil = form.cleaned_data['soil_type']
                    season = form.cleaned_data['season']
                    rainfall = form.cleaned_data['rainfall_level']

                    # One-hot encoding must match training pipeline. Training script will define order
                    # Here we recreate feature vector in the same order as training
                    categorical_orders = {
                        'soil_type': ['clay', 'sandy', 'loamy', 'silt', 'peat', 'chalk'],
                        'season': ['winter', 'summer', 'monsoon'],
                        'rainfall_level': ['low', 'medium', 'high'],
                    }

                    features = []
                    for value, allowed in [
                        (soil, categorical_orders['soil_type']),
                        (season, categorical_orders['season']),
                        (rainfall, categorical_orders['rainfall_level']),
                    ]:
                        for category in allowed:
                            features.append(1 if value == category else 0)

                    y_pred = model.predict([features])[0]
                    prediction = label_encoder.inverse_transform([y_pred])[0]
                    recommended_crops = [prediction]
                except Exception as exc:
                    messages.error(request, f'Prediction failed: {exc}')

    context = {
        'form': form,
        'prediction': prediction,
        'recommended_crops': recommended_crops,
        'model_loaded': model_loaded,
    }
    return render(request, 'pages/crop_suggestion.html', context)    

def market_data(request):
    # Filters: region (for rainfall), price (for crop prices)
    region = (request.GET.get('region') or '').strip()
    price_q = (request.GET.get('price') or '').strip()
    prices = []
    rainfall = []
    try:
        # Fetch all prices first; we'll apply precise filtering below
        prices = get_crop_prices(region=None)
    except Exception as exc:
        messages.error(request, f"Failed to fetch prices: {exc}")
    try:
        rainfall = get_rainfall(region=region or None)
    except Exception as exc:
        messages.error(request, f"Failed to fetch rainfall: {exc}")

    # Extra robust filtering on server side to ensure UI filter always works
    def _norm(val: object) -> str:
        return str(val or '').strip().lower()

    # Apply dedicated filters
    if price_q:
        qp = _norm(price_q)
        prices = [
            p for p in prices
            if qp in _norm(p.get('market')) or qp in _norm(p.get('commodity')) or qp in _norm(p.get('variety'))
        ]
    if region:
        qr = _norm(region)
        rainfall = [
            r for r in rainfall
            if qr in _norm(r.get('region')) or qr in _norm(r.get('period'))
        ]

    context = {
        'region': region,
        'price': price_q,
        'prices': prices,
        'rainfall': rainfall,
    }
    return render(request, 'pages/market_data.html', context)

def tips(request):
    from .models import Tip
    qs = Tip.objects.all()

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    crop = request.GET.get('crop', '').strip()
    season = request.GET.get('season', '').strip()

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if category:
        qs = qs.filter(category=category)
    if crop:
        qs = qs.filter(crop__icontains=crop)
    if season:
        qs = qs.filter(season__icontains=season)

    context = {
        'tips': qs[:100],  # simple cap
        'q': q,
        'category': category,
        'crop': crop,
        'season': season,
        'categories': dict(Tip.CATEGORY_CHOICES),
    }
    return render(request, 'pages/tips.html', context)

@csrf_protect
@staff_member_required
def admin_dashboard(request):
    # Handle POST actions: upload dataset and retrain model
    data_dir = os.path.join(settings.BASE_DIR, 'core', 'ml', 'data')
    os.makedirs(data_dir, exist_ok=True)
    dataset_csv = os.path.join(data_dir, 'crop_dataset.csv')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload_dataset':
            file = request.FILES.get('dataset')
            if not file:
                messages.error(request, 'Please choose a CSV file to upload.')
            else:
                try:
                    # Save uploaded file to dataset path
                    with open(dataset_csv, 'wb+') as dest:
                        for chunk in file.chunks():
                            dest.write(chunk)
                    messages.success(request, 'Dataset uploaded successfully.')
                except Exception as exc:
                    messages.error(request, f'Failed to save dataset: {exc}')
        elif action == 'retrain_model':
            try:
                train_model.train_and_save()
                messages.success(request, 'Model retrained and saved successfully.')
            except Exception as exc:
                messages.error(request, f'Failed to retrain model: {exc}')

    # Build pie chart using existing analytics (if available)
    try:
        charts = build_from_dataset(dataset_csv_path=dataset_csv)
        ctx = {
            'pie_b64': charts.pie_region_queries_b64,
        }
    except Exception as exc:
        messages.error(request, f"Failed to build charts: {exc}")
        ctx = {}

    # Region vs Rainfall chart from Gujarat rainfall CSV used in market-data
    try:
        rainfall_items = get_rainfall(region=None)
        # Convert rainfall to numeric and aggregate by region (latest values dominate if duplicates)
        from collections import defaultdict
        by_region = defaultdict(float)

        def to_number(text: str) -> float:
            s = ''.join(ch for ch in str(text) if (ch.isdigit() or ch == '.' or ch == ','))
            s = s.replace(',', '')
            try:
                return float(s)
            except Exception:
                return 0.0

        for row in rainfall_items:
            region_name = str(row.get('region', '')).strip() or 'Unknown'
            mm = to_number(row.get('rainfall_mm', '0'))
            # Keep the max rainfall per region to reflect peak reading
            if mm > by_region[region_name]:
                by_region[region_name] = mm

        items = list(by_region.items())
        # Sort by rainfall desc and take top 8
        items.sort(key=lambda x: x[1], reverse=True)
        top = items[:8]

        rainfall_bar_b64 = None
        if top:
            labels = [t[0] for t in top]
            values = [t[1] for t in top]
            x = list(range(len(labels)))
            plt.figure(figsize=(6, 3))
            # Scatter points
            plt.scatter(x, values, color='#6FB3D1', s=60, edgecolors='#2563EB', linewidths=0.6)
            # Connect the dots with a line
            plt.plot(x, values, color='#2563EB', linewidth=1.2, alpha=0.7)
            plt.ylabel('Rainfall (mm)')
            plt.xticks(x, labels, rotation=20, ha='right', fontsize=9)
            plt.grid(True, which='both', axis='both', linestyle='--', alpha=0.3)
            plt.tight_layout()
            # no per-point annotations
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=160)
            plt.close()
            buf.seek(0)
            rainfall_bar_b64 = base64.b64encode(buf.read()).decode('ascii')

        ctx.update({'rainfall_bar_b64': rainfall_bar_b64})
    except Exception as exc:
        messages.error(request, f"Failed to build rainfall chart: {exc}")

    # Commodity vs Price chart + prices table from Gujarat prices CSV
    try:
        prices = get_crop_prices(region=None)
        # Normalize and compute average price per commodity
        from collections import defaultdict
        sums = defaultdict(float)
        counts = defaultdict(int)

        def to_number(text: str) -> float:
            s = ''.join(ch for ch in str(text) if (ch.isdigit() or ch == '.' or ch == ','))
            s = s.replace(',', '')
            try:
                return float(s)
            except Exception:
                return 0.0

        for row in prices:
            commodity = str(row.get('commodity', '')).strip() or 'Unknown'
            price_val = to_number(row.get('price', '0'))
            if price_val > 0:
                sums[commodity] += price_val
                counts[commodity] += 1

        # Prepare data for plotting (top N commodities by avg price)
        avg_items = [
            (k, (sums[k] / counts[k]) if counts[k] else 0.0)
            for k in sums.keys()
        ]
        # Sort by average price desc and take top 8 for readability
        avg_items.sort(key=lambda x: x[1], reverse=True)
        top = avg_items[:8]

        prices_bar_b64 = None
        if top:
            labels = [t[0] for t in top]
            values = [t[1] for t in top]
            plt.figure(figsize=(6, 3))
            bars = plt.bar(labels, values, color='#6FAF6F')
            plt.ylabel('Avg Price (₹/quintal)')
            plt.xticks(rotation=20, ha='right', fontsize=9)
            plt.tight_layout()
            # Add value labels on bars
            for b in bars:
                h = b.get_height()
                plt.text(b.get_x() + b.get_width()/2, h, f"{h:.0f}", ha='center', va='bottom', fontsize=8)
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=160)
            plt.close()
            buf.seek(0)
            prices_bar_b64 = base64.b64encode(buf.read()).decode('ascii')

        # Update context with the bar chart only (table removed from UI)
        ctx.update({
            'prices_bar_b64': prices_bar_b64,
        })
    except Exception as exc:
        messages.error(request, f"Failed to build prices chart/table: {exc}")

    return render(request, 'pages/admin_dashboard.html', ctx)

def contact(request):
    form = ContactMessageForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Thanks! Your message has been sent.')
            return redirect('contact')  # PRG pattern
        else:
            messages.error(request, 'Please fix the errors below and resubmit.')
    return render(request, 'pages/contact.html', {
        'form': form,
        'suppress_global_messages': True,
    })

def schemes(request):
    items = []
    try:
        items = get_schemes(limit=15)
    except Exception as exc:
        messages.error(request, f"Failed to fetch schemes/news: {exc}")
    return render(request, 'pages/schemes.html', { 'items': items })

def download_insights_csv(request):
    """Provide a simple CSV of crop frequency (from dataset) as a downloadable file."""
    import csv
    dataset_csv = os.path.join(settings.BASE_DIR, 'core', 'ml', 'data', 'crop_dataset.csv')
    # Read counts
    try:
        import pandas as pd
        df = pd.read_csv(dataset_csv)
        counts = df['crop'].astype(str).str.strip().str.title().value_counts()
    except Exception:
        counts = {'Wheat': 2, 'Rice': 2, 'Maize': 1}

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="insights_crops.csv"'
    writer = csv.writer(response)
    writer.writerow(['Crop', 'Count'])
    if hasattr(counts, 'items'):
        items = counts.items()
    else:
        items = counts.to_dict().items()
    for crop, count in items:
        writer.writerow([crop, count])
    return response

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


@dataclass
class ChartImages:
    bar_most_recommended_b64: str
    line_price_trends_b64: str
    pie_region_queries_b64: str


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def build_from_dataset(
    dataset_csv_path: str,
    region_query_counts: Dict[str, int] | None = None,
) -> ChartImages:
    """
    Build charts using the training dataset for bar chart, and synthetic data for prices & regions if needed.
    - dataset_csv_path should have a 'crop' column (e.g., core/ml/data/crop_dataset.csv)
    - region_query_counts: optional dict like {"Delhi": 10, "Mumbai": 5}
    """
    # Load dataset for crop counts
    try:
        df = pd.read_csv(dataset_csv_path)
    except Exception:
        df = pd.DataFrame({"crop": ["wheat", "rice", "maize", "wheat", "rice"]})

    crop_counts = df["crop"].astype(str).str.strip().str.title().value_counts().sort_values(ascending=False)

    # Bar: Most recommended crops
    fig1, ax1 = plt.subplots(figsize=(6, 3.5))
    crop_counts.plot(kind="bar", color="#16a34a", ax=ax1)
    ax1.set_title("Most Recommended Crops")
    ax1.set_xlabel("Crop")
    ax1.set_ylabel("Count")
    bar_b64 = _fig_to_base64(fig1)

    # Line: Price trends (synthetic demo series)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=12, freq="MS")
    series = pd.Series([2000, 2050, 1980, 2100, 2150, 2200, 2180, 2250, 2300, 2280, 2350, 2400], index=dates)
    fig2, ax2 = plt.subplots(figsize=(6, 3.5))
    ax2.plot(series.index, series.values, marker="o", color="#2563eb")
    ax2.set_title("Price Trend (Demo)")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Price (₹/qtl)")
    ax2.grid(alpha=0.3)
    for x, y in zip(series.index, series.values):
        ax2.annotate(f"{int(y)}", (x, y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    fig2.autofmt_xdate()
    line_b64 = _fig_to_base64(fig2)

    # Pie: Region queries
    rq = region_query_counts or {"Delhi": 12, "Mumbai": 7, "Bengaluru": 5, "Chennai": 4}
    labels = list(rq.keys())
    sizes = list(rq.values())
    fig3, ax3 = plt.subplots(figsize=(5, 3.5))
    ax3.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=140)
    ax3.set_title("Region Queries (Demo)")
    pie_b64 = _fig_to_base64(fig3)

    return ChartImages(bar_most_recommended_b64=bar_b64,
                       line_price_trends_b64=line_b64,
                       pie_region_queries_b64=pie_b64)

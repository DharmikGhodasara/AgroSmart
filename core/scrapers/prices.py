from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import os
from django.conf import settings
import pandas as pd


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}


def get_crop_prices(region: str | None = None) -> List[Dict[str, str]]:
    """
    Scrape crop prices by region.

    NOTE: Many official portals use dynamic content or have anti-scraping. For demo reliability, this function
    first tries to read a local Gujarat CSV, then scrapes a public HTML table example when available,
    and finally falls back to sample data if all else fails.
    """
    # 1) Preferred source: local CSV core/ml/data/gujarat_crop_prices.csv
    try:
        csv_path = os.path.join(settings.BASE_DIR, 'core', 'ml', 'data', 'gujarat_crop_prices.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Expected columns: Commodity, Variety, Price (₹/quintal), Market
            out: List[Dict[str, str]] = []
            for _, row in df.iterrows():
                commodity = str(row.get('Commodity', '')).strip()
                variety = str(row.get('Variety', '')).strip()
                price = str(row.get('Price (₹/quintal)', '')).strip()
                market = str(row.get('Market', '')).strip()
                if not commodity or not market:
                    continue
                out.append({
                    'commodity': commodity,
                    'variety': variety,
                    'price': price,
                    'market': market,
                })
            if region:
                out = [r for r in out if region.lower() in r.get('market', '').lower()]
            if out:
                return out
    except Exception:
        # If CSV read fails, proceed to web/placeholder
        pass

    # 2) Secondary attempt: placeholder scrape
    url = "https://www.agrimarketwatch.com/sample-prices"  # placeholder example-like URL

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.ok and "<table" in resp.text:
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            rows = table.find_all("tr") if table else []
            out: List[Dict[str, str]] = []
            for tr in rows[1:]:
                tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if len(tds) >= 4:
                    out.append({
                        "commodity": tds[0],
                        "variety": tds[1],
                        "price": tds[2],
                        "market": tds[3],
                    })
            if region:
                out = [r for r in out if region.lower() in r.get("market", "").lower()]
            if out:
                return out
    except Exception:
        pass

    # Fallback sample data
    sample = [
        {"commodity": "Wheat", "variety": "Durum", "price": "₹2,150/qtl", "market": "Delhi"},
        {"commodity": "Rice", "variety": "Basmati", "price": "₹3,200/qtl", "market": "Punjab"},
        {"commodity": "Maize", "variety": "Yellow", "price": "₹1,750/qtl", "market": "Karnataka"},
    ]
    if region:
        sample = [r for r in sample if region.lower() in r["market"].lower()]
    return sample

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


def get_rainfall(region: str | None = None) -> List[Dict[str, str]]:
    """
    Scrape rainfall information by region.

    For demo reliability, attempts to parse a simple table from a placeholder URL,
    else returns static sample data.
    """
    # 1) Preferred source: local CSV core/ml/data/gujarat_rainfall_data.csv
    try:
        csv_path = os.path.join(settings.BASE_DIR, 'core', 'ml', 'data', 'gujarat_rainfall_data.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Expected columns: City, Rainfall (mm), Time Period
            out: List[Dict[str, str]] = []
            for _, row in df.iterrows():
                region_name = str(row.get('City', '')).strip()
                rainfall_mm = str(row.get('Rainfall (mm)', '')).strip()
                period = str(row.get('Time Period', '')).strip()
                if not region_name:
                    continue
                out.append({
                    'region': region_name,
                    'rainfall_mm': rainfall_mm,
                    'period': period,
                    'source': 'Gujarat CSV',
                })
            if region:
                out = [r for r in out if region.lower() in r.get('region', '').lower()]
            if out:
                return out
    except Exception:
        # If CSV read fails, fall back to web/placeholder and then to sample
        pass

    # 2) Secondary attempt: placeholder scraping (kept as fallback)
    url = "https://www.example.com/weather/rainfall-table"  # placeholder
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.ok and "<table" in resp.text:
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            rows = table.find_all("tr") if table else []
            out2: List[Dict[str, str]] = []
            for tr in rows[1:]:
                tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if len(tds) >= 3:
                    out2.append({
                        "region": tds[0],
                        "rainfall_mm": tds[1],
                        "period": tds[2],
                        "source": "Parsed table",
                    })
            if region:
                out2 = [r for r in out2 if region.lower() in r.get("region", "").lower()]
            if out2:
                return out2
    except Exception:
        pass

    sample = [
        {"region": "Delhi", "rainfall_mm": "12.4", "period": "Last 24h", "source": "Sample"},
        {"region": "Mumbai", "rainfall_mm": "45.8", "period": "Last 24h", "source": "Sample"},
        {"region": "Bengaluru", "rainfall_mm": "5.2", "period": "Last 24h", "source": "Sample"},
    ]
    if region:
        sample = [r for r in sample if region.lower() in r["region"].lower()]
    return sample

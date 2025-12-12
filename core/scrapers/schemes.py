from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}


def get_schemes(limit: int | None = 10) -> List[Dict[str, str]]:
    """
    Scrape latest government schemes from Gujarat Agriculture site.
    Falls back to sample items if scraping fails.
    """
    url = "https://agri.gujarat.gov.in/Scheme"
    items: List[Dict[str, str]] = []

    try:
        # Selenium-only scraping (per user request)
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        try:
            driver.get(url)
            time.sleep(5)  # wait for JavaScript to load
            html = driver.page_source
        finally:
            driver.quit()

        soup = BeautifulSoup(html, "html.parser")

        # 1) Site-specific: parse schemes table
        rows = soup.select("#tblSchemes tbody tr")
        if rows:
            current_dept = ""
            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) < 3:
                    continue

                # Two layouts expected due to rowspan on Department column:
                # A) 4 tds => [serial, department, scheme, link]
                # B) 3 tds => [serial, scheme, link] (department carried from previous row)
                serial = tds[0].get_text(strip=True)
                if len(tds) >= 4:
                    dept_cell = tds[1]
                    dept_text = dept_cell.get_text(strip=True)
                    if dept_text:
                        current_dept = dept_text
                    department = current_dept
                    scheme_td_index = 2
                    link_td_index = 3
                else:  # len == 3
                    department = current_dept
                    scheme_td_index = 1
                    link_td_index = 2

                # Scheme name and link
                scheme_name = tds[scheme_td_index].get_text(strip=True) if len(tds) > scheme_td_index else ""
                link_tag = tds[link_td_index].find("a") if len(tds) > link_td_index else None
                href = link_tag.get("href") if link_tag else ""
                full_url = urljoin(url, href) if href else url

                if scheme_name or department:
                    title = scheme_name or department
                    cols = [serial, department, scheme_name, full_url]
                    items.append({"title": title, "url": full_url, "cols": cols})

        if items:
            if limit is not None:
                items = items[:limit]
            return items

    except Exception as e:
        print(f"[Error] Could not scrape schemes: {e}")

    # Fallback: return empty list if nothing scraped
    return []

import json
import os
import re
import requests
from bs4 import BeautifulSoup

CACHE_DIR = "data"
CACHE_FILE = os.path.join(CACHE_DIR, "founding_date_cache.json")


def load_founding_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        print("Warning: founding cache corrupt. Starting fresh.")
        return {}


def save_founding_cache(cache: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print(f"Saved founding date cache ({len(cache)} entries)")


def get_founding_date(ticker: str, company_name: str = None) -> str:
    """
    Get founding/establishment date as a string (e.g. "1976" or "April 1, 1976").
    Uses Wikipedia infobox with caching.
    Returns "N/A" on failure.
    """
    ticker = ticker.upper()
    cache = load_founding_cache()

    if ticker in cache:
        print(f"Cache hit for {ticker}: {cache[ticker]}")
        return cache[ticker]

    try:
        if not company_name:
            company_name = ticker

        company_clean = re.sub(
            r'\s+(Inc\.|Corp\.|Co\.|Holdings|Limited|Ltd\.?|PLC|& Company)$',
            '', company_name, flags=re.IGNORECASE
        ).strip()
        base_name = company_clean.replace(" ", "_").replace("&", "%26")

        urls_to_try = [
            f"https://en.wikipedia.org/wiki/{base_name}_Inc.",
            f"https://en.wikipedia.org/wiki/{base_name}_Inc",
            f"https://en.wikipedia.org/wiki/{base_name}",
            f"https://en.wikipedia.org/wiki/{ticker}",
        ]

        headers = {"User-Agent": "StockAnalyzer/1.0 (your.email@example.com)"}
        founding_date = "N/A"

        for url in urls_to_try:
            try:
                response = requests.get(url, headers=headers, timeout=8)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                infobox = soup.find("table", class_="infobox")
                if not infobox:
                    continue

                founded_label = infobox.find(
                    "th", string=re.compile(r"Founded|Established|Incorporated", re.I)
                )
                if founded_label:
                    founded_cell = founded_label.find_next("td")
                    if founded_cell:
                        text = founded_cell.get_text(separator=" ", strip=True)
                        # Try to extract a nice date string
                        # Look for patterns like "April 1, 1976", "1976", "April 1, 1976; 48 years ago"
                        date_match = re.search(
                            r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b|\b\d{4}\b)",
                            text, re.I
                        )
                        if date_match:
                            founding_date = date_match.group(0).strip()
                            break  # good enough
                        # Fallback: just grab first 4-digit year
                        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
                        if year_match:
                            founding_date = year_match.group(0)
                            break
            except:
                continue

        cache[ticker] = founding_date
        save_founding_cache(cache)
        return founding_date

    except Exception as e:
        print(f"Failed for {ticker}: {e}")
        cache[ticker] = "N/A"
        save_founding_cache(cache)
        return "N/A"
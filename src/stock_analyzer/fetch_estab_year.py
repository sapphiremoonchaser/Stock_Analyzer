import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Make paths relative to THIS FILE's location → reliable no matter how you run it
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]          # assumes file is in src/ → root is one level up
CACHE_DIR = PROJECT_ROOT / "data"
CACHE_FILE = CACHE_DIR / "established_cache.json"


def load_founding_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with CACHE_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: established cache corrupt or unreadable ({e}). Starting fresh.")
        return {}


def save_founding_cache(cache: dict):
    print(f"[SAVE DEBUG] Starting save to {CACHE_FILE}")
    print(f"[SAVE DEBUG] Data to save: {cache}")

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[SAVE DEBUG] Directory ensured: {CACHE_DIR.exists()} ({CACHE_DIR.absolute()})")

        with CACHE_FILE.open('w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
            f.flush()  # force disk write
            os.fsync(f.fileno())  # even stronger on some systems

        print(f"[SAVE DEBUG] Save finished. File exists? {CACHE_FILE.exists()}")
        if CACHE_FILE.exists():
            print(f"[SAVE DEBUG] File size after write: {CACHE_FILE.stat().st_size} bytes")
        else:
            print("[SAVE DEBUG] File STILL does not exist after write attempt!")
    except Exception as e:
        print(f"[SAVE ERROR] Failed to write cache: {type(e).__name__}: {e}")
        print(f"[SAVE ERROR] Full path attempted: {CACHE_FILE.absolute()}")


def get_founding_date(
    ticker: str,
    company_name: str = None
) -> str:
    ticker = ticker.upper()
    cache = load_founding_cache()

    if ticker in cache:
        print(f"[CACHE DEBUG] Hit: {ticker} -> {cache[ticker]}")
        return cache[ticker]

    print(f"[CACHE DEBUG] Miss for {ticker}. Starting scrape.")
    founding_date = "N/A"  # default

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

        print(f"[CACHE DEBUG] Scraped date: '{founding_date}' for {ticker}")

        # FORCE assign to cache
        cache[ticker] = founding_date
        print(f"[CACHE DEBUG] Cache updated in memory: {ticker} = {cache[ticker]}")
        print(f"[CACHE DEBUG] Full cache dict now: {cache}")

        # FORCE call save
        print("[CACHE DEBUG] Calling save_founding_cache NOW")
        save_founding_cache(cache)
        print("[CACHE DEBUG] save_founding_cache returned successfully")

    except Exception as exc:
        print(f"[CACHE DEBUG] EXCEPTION during scrape/save for {ticker}: {type(exc).__name__}: {exc}")
        # Still try to save failure
        cache[ticker] = "N/A"
        save_founding_cache(cache)

    # One final force-save attempt at the very end
    print("[CACHE DEBUG] Final force-check before return")
    save_founding_cache(cache)  # <--- this should almost always run

    return founding_date
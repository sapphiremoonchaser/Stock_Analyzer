from email.contentmanager import raw_data_manager
from http.client import responses
from operator import ifloordiv
from typing import (
    List,
    Union,
    Optional
)
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fontTools.misc.cython import returns
from fontTools.ttLib.tables.otTraverse import dfs_base_table
from numpy.ma.extras import row_stack

# Alias to make return type easier to read and reuse
StockInfo = dict[str, Union[str, float, int]]
ErrorInfo = dict[str, str] # {"error": "message"}


def get_stock_info(
        tickers: str | List[str]
) -> dict[str, Union[StockInfo, ErrorInfo]]:
    f"""
    Fetch basic stock information for one or more tickers.
    
    :param tickers (str or list[str]): tickers to fetch 
    :return (dict): 
    """
    # If tickers is a str then uppercase it and turn it into a list with one element
    if isinstance(tickers, str):
        tickers = [tickers.upper()]
    # If tickers can be iterated uppercase all elements
    else:
        tickers = [t.upper() for t in tickers]

    result = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or 'longName' not in info:
                result[ticker] = {"error": "No data returned"}
                continue

            # Create a dict from the info object
            result[ticker] = {
                "name": info.get("longName"),
                "price": info.get("currentPrice"),
                "industry": info.get("industry"),
                "sector": info.get("sector"),
                "dividend_yield": info.get("dividendYield"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "average_volume": info.get("averageVolume"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "price_to_book": info.get("priceToBook")
            }

        except Exception as e:
            result[ticker] = {"error": str(e)}

    return result


def get_competitors(ticker: str, max_competitors: int = 6) -> List[str]:
    """
    Scrape competitor/peer tickers from the "Compare To" section on Yahoo Finance's
    main quote page for the given ticker.

    Returns a list of peer tickers (excluding the input ticker itself).
    Returns empty list if section not found or error occurs.
    """
    ticker = ticker.upper()
    url = f"https://finance.yahoo.com/quote/{ticker}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Try multiple possible selectors for the compare section/cards
        # 1. Look for cards containing tickers (common pattern: a[href*="/quote/"])
        potential_links = soup.find_all("a", href=lambda h: h and "/quote/" in h)

        peers = []
        seen = set([ticker])  # avoid duplicates & self

        for link in potential_links:
            href = link.get("href", "")
            if "/quote/" in href:
                peer_ticker = href.split("/quote/")[-1].split("?")[0].split("/")[0].upper()
                if peer_ticker and peer_ticker.isalnum() and peer_ticker not in seen:
                    # Quick filter: likely a ticker if short & uppercase-able
                    if 1 <= len(peer_ticker) <= 5 and peer_ticker.isalpha() or '.' in peer_ticker:
                        peers.append(peer_ticker)
                        seen.add(peer_ticker)
                        if len(peers) >= max_competitors:
                            break

        # Fallback: if few found, look for text in tables or spans near "Compare"
        if len(peers) < 3:
            compare_section = soup.find(string=lambda t: t and "Compare To" in t)
            if compare_section:
                parent = compare_section.find_parent(["div", "section"])
                if parent:
                    extra_tickers = [
                        span.text.strip().upper()
                        for span in parent.find_all(["span", "td", "div"])
                        if span.text.strip().isupper() and 1 <= len(span.text.strip()) <= 5
                    ]
                    for t in extra_tickers:
                        if t not in seen:
                            peers.append(t)
                            seen.add(t)
                            if len(peers) >= max_competitors:
                                break

        return peers[:max_competitors]

    except Exception as e:
        print(f"Error scraping competitors for {ticker}: {str(e)}")
        return []


def compare_with_competitors(
    main_ticker: str,
    max_competitors: int = 5,
    include_summary: bool = False
) -> Optional[pd.DataFrame]:
    """
    Fetch data for a main ticker and up to 5 of its competitors and
    return a dataframe ready to display or compare.

    Key Columns:
        -  name, price, industry, sector, dividend_yield, trailing_pe,
        forward_pe, average_volume, market_cap, enterprise_value,
        price_to_book
    :param main_ticker: ticker to find competitors for
    :param max_competitors: maximum number of competitors to return
    :param include_summary:
    :return:
    """
    main_ticker = main_ticker.upper()

    # Get Competitors
    competitors = get_competitors(
        main_ticker,
        max_competitors=max_competitors
    )
    if not competitors:
        print(f"No competitors found for {main_ticker}")
        competitors = []

    # All tickers to fetch
    all_tickers = [main_ticker] + competitors

    # Fetch info for all
    raw_data = get_stock_info(all_tickers)

    # Build rows for DataFrame
    rows = []
    for ticker in all_tickers:
        info = raw_data.get(ticker, {})
        if "error" in info:
            rows.append({
                "ticker": ticker,
                "name": f"ERROR: {info['error']}",
                "price": None,
                "industry": "N/A",
                "sector": "N/A",
                "dividend_yield": None,
                "trailing_pe": None,
                "forward_pe": None,
                "average_volume": None,
                "market_cap": None,
                "enterprise_value": None,
                "price_to_book": None
            })
            continue

        row = {
            "ticker": ticker,
            "name": info.get("name", "N/A"),
            "price": info.get("currentPrice"),
            "industry": info.get("industry"),
            "sector": info.get("sector"),
            "dividend_yield": info.get("dividendYield"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "average_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "price_to_book": info.get("priceToBook")
        }
        if include_summary:
            row["summary"] = info.get("summary", "N/A")

        rows.append(row)

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df.set_index("ticker", inplace=True)

    # Nice formatting
    # Price in dollars with 2 decimals
    if "price" in df.columns:
        df['price'] = df['price'].apply(
            lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "N/A"
        )

    # Dividend Yield in percentage 0 decimals
    if "dividend_yield" in df.columns:
        df['dividen_yield'] = df['dividend_yield'].apply(
            lambda x: f"{x:.0f}%" if pd.notnull(x) and x > 0 else "N/A"
        )

    # Trailing PE as 2 decimals
    if "trailing_pe" in df.columns:
        df['trailing_pe'] = df['trailing_pe'].apply(
            lambda x: f"{x:.2f}%" if pd.notnull(x) and x > 0 else "N/A"
        )

    # Forward PE as 2 decimals
    if "forward_pe" in df.columns:
        df['forward_pe'] = df['forward_pe'].apply(
            lambda x: f"{x:.2f}%" if pd.notnull(x) and x > 0 else "N/A"
        )

    # Average Volume in thousands
    if "average_volume" in df.columns:
        df['average_volume'] = df['average_volume'].apply(
            lambda x: f"{x:,.0f}%" if pd.notnull(x) and x > 0 else "N/A"
        )

    # Market Cap in Billions
    if "market_cap" in df.columns:
        df['market_cap'] = df['market_cap'].apply(
            lambda x: f"{x / 1_000_000_000:.2f}B" if pd.notnull(x) and x > 0 else "N/A"
        )

    # Enterprise Value in Billions
    if "enterprise_value" in df.columns:
        df['enterprise_value'] = df['enterprise_value'].apply(
            lambda x: f"{x / 1_000_000_000:.2f}B" if pd.notnull(x) and x > 0 else "N/A"
        )

    # Price to Book ration with 2 decimals
    if "price_to_book" in df.columns:
        df['price_to_book'] = df['price_to_book'].apply(
            lambda x: f"{x:.2f}%" if pd.notnull(x) and x > 0 else "N/A"
        )

    return df


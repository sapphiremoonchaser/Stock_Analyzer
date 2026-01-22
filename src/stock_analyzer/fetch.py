from http.client import responses
from typing import (
    List,
    Union
)
import yfinance as yf
import requests
from bs4 import BeautifulSoup

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


def get_yahoo_peers(
        ticker: str,
        max_peers: int=5
) -> List[str]:
    """
    Scrape Yahoo Finance Peers section for competitor tickers.
    returns a list of up to max_peers tickers (excluding the input one).

    Note: Web scraping can break if Yahoo's layout changes
    returns empty list on failure.
    :param ticker: the ticker whose competitors you want to find
    :param max_peers: max competitors you want
    :return: List of competitors for the input ticker
    """
    ticker = ticker.upper()
    url = f"https://finance.yahoo.com/quote/{ticker}/peers"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        soup = BeautifulSoup(response.text, "html.parser")

        # Find the peers table or list - selector
        # May need occassional update
        # Look for table rows in the competitors/peers section
        peer_rows = soup.select("table tbody tr")

        peers = []
        for row in peer_rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                peer_ticker_tag = cells[0].find("a") or cells[0].find("span")
                if peer_ticker_tag and peer_ticker_tag.text.strip():
                    peer_ticker = peer_ticker_tag.text.strip().upper()
                    if peer_ticker != ticker and peer_ticker not in peers:
                        peers.append(peer_ticker)
                        if len(peers) >= max_peers:
                            break

        return peers

    except Exception as e:
        print(f"Error fetching peers for {ticker}: {e}")
        return []


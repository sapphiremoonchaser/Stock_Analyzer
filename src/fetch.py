from typing import (
    List,
    Union
)
import yfinance as yf

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
    # Normalize the case of the tickers
    if isinstance(tickers, str):
        tickers = [tickers.upper()]
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

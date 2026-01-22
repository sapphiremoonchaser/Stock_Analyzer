import pytest
from src.fetch import get_stock_info

def test_get_stock_info_single_valid_ticker():
    result = get_stock_info('AAPL')

    # Test return type
    assert isinstance(result, dict)

    # Test that the requeted ticker is in the returned dict
    # assert 'AAPL' in result
    #
    # info = result['AAPL']
    #
    # assert "error" not in info
    #
    # # Test attribute types
    # assert isinstance(info["name"], str)
    # assert isinstance(info["price"], (int, float, type(None)))
    # assert isinstance(info['industry'], (str, type(None)))
    # assert isinstance(info['sector'], (str, type(None)))
    # assert isinstance(info['dividend_yield'], (int, float, type(None)))
    # assert isinstance(info['trailing_pe'], (int, float, type(None)))
    # assert isinstance(info['forward_pe'], (int, float, type(None)))
    # assert isinstance(info['average_volume'], (int, float, type(None)))
    # assert isinstance(info["market_cap"], (int, float, type(None)))
    # assert isinstance(info["enterprise_value"], (int, float, type(None)))
    # assert isinstance(info["price_to_book"], (int, float, type(None)))




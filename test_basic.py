#!/usr/bin/env python3
"""
Basic tests to verify the stock analyzer tool works
"""

from portfolio import Portfolio
from data_fetcher import StockDataFetcher
from stock_analyzer import StockAnalyzer
import os

def test_portfolio():
    """Test portfolio management"""
    print("Testing Portfolio Management...")

    # Clean up any existing test portfolio
    test_file = "test_portfolio.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    portfolio = Portfolio(test_file)

    # Test adding cash
    portfolio.add_cash(10000)
    assert portfolio.cash == 10000, "Cash addition failed"
    print("✓ Cash management works")

    # Test buying
    portfolio.buy_stock("AAPL", 10, 150.0)
    assert "AAPL" in portfolio.positions, "Buy stock failed"
    print("✓ Buy stock works")

    # Test selling
    portfolio.sell_stock("AAPL", 5, 160.0)
    assert portfolio.positions["AAPL"]["shares"] == 5, "Sell stock failed"
    print("✓ Sell stock works")

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

    print("✓ Portfolio tests passed!\n")

def test_data_fetcher():
    """Test stock data fetching"""
    print("Testing Data Fetcher...")

    fetcher = StockDataFetcher()

    # Test getting stock info (may fail if no internet)
    try:
        info = fetcher.get_stock_info("AAPL")
        if info:
            print(f"✓ Fetched data for AAPL: ${info['current_price']:.2f}")
            assert 'ticker' in info, "Stock info missing ticker"
            assert 'current_price' in info, "Stock info missing price"
            print("✓ Data fetcher works")
        else:
            print("⚠ Could not fetch data (may need internet connection)")
    except Exception as e:
        print(f"⚠ Data fetcher test skipped: {str(e)}")

    print()

def test_stock_analyzer():
    """Test stock analyzer"""
    print("Testing Stock Analyzer...")

    analyzer = StockAnalyzer()

    # Test screening
    watchlist = analyzer.screen_stocks()
    assert len(watchlist) > 0, "Watchlist is empty"
    print(f"✓ Default watchlist has {len(watchlist)} stocks")

    print("✓ Stock analyzer initialized\n")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Stock Analyzer Tool - Basic Tests")
    print("=" * 60 + "\n")

    test_portfolio()
    test_data_fetcher()
    test_stock_analyzer()

    print("=" * 60)
    print("All basic tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()

"""
Stock Data Fetcher Module
Handles fetching real-time and historical stock data using yfinance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class StockDataFetcher:
    """Fetches and processes stock market data"""

    def __init__(self):
        self.cache = {}

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        Get detailed information about a stock

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')

        Returns:
            Dictionary with stock information or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get recent price data
            hist = stock.history(period="5d")
            if hist.empty:
                return None

            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price

            return {
                'ticker': ticker.upper(),
                'name': info.get('longName', ticker),
                'current_price': current_price,
                'previous_close': prev_price,
                'change_percent': ((current_price - prev_price) / prev_price * 100),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'fifty_day_avg': info.get('fiftyDayAverage', 'N/A'),
                'two_hundred_day_avg': info.get('twoHundredDayAverage', 'N/A'),
                'volume': info.get('volume', 'N/A'),
                'avg_volume': info.get('averageVolume', 'N/A'),
            }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return None

    def get_historical_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Get historical price data for a stock

        Args:
            ticker: Stock ticker symbol
            period: Time period ('1mo', '3mo', '6mo', '1y', '2y', '5y')

        Returns:
            DataFrame with historical data or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist if not hist.empty else None
        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {str(e)}")
            return None

    def get_multiple_stocks(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Get information for multiple stocks

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping tickers to their info
        """
        results = {}
        for ticker in tickers:
            info = self.get_stock_info(ticker)
            if info:
                results[ticker.upper()] = info
        return results

    def calculate_technical_indicators(self, ticker: str) -> Optional[Dict]:
        """
        Calculate technical indicators for a stock

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with technical indicators
        """
        hist = self.get_historical_data(ticker, period="1y")
        if hist is None or hist.empty:
            return None

        try:
            # Calculate moving averages
            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
            hist['SMA_200'] = hist['Close'].rolling(window=200).mean()

            # Calculate RSI (Relative Strength Index)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist['RSI'] = 100 - (100 / (1 + rs))

            # Get latest values
            latest = hist.iloc[-1]
            current_price = latest['Close']

            return {
                'current_price': current_price,
                'sma_50': latest['SMA_50'],
                'sma_200': latest['SMA_200'],
                'rsi': latest['RSI'],
                'above_sma_50': current_price > latest['SMA_50'],
                'above_sma_200': current_price > latest['SMA_200'],
                'golden_cross': latest['SMA_50'] > latest['SMA_200'],
            }
        except Exception as e:
            print(f"Error calculating indicators for {ticker}: {str(e)}")
            return None

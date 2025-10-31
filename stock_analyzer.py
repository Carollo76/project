"""
Stock Analyzer Module
Analyzes stocks and provides buy/sell recommendations
"""

from typing import Dict, List, Tuple
from data_fetcher import StockDataFetcher
from portfolio import Portfolio


class StockAnalyzer:
    """Analyzes stocks and generates buy/sell recommendations"""

    def __init__(self):
        self.data_fetcher = StockDataFetcher()

    def analyze_stock(self, ticker: str) -> Dict:
        """
        Perform comprehensive analysis on a stock

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with analysis results and recommendation
        """
        # Get basic info
        info = self.data_fetcher.get_stock_info(ticker)
        if not info:
            return {'error': f'Unable to fetch data for {ticker}'}

        # Get technical indicators
        indicators = self.data_fetcher.calculate_technical_indicators(ticker)
        if not indicators:
            return {'error': f'Unable to calculate indicators for {ticker}'}

        # Analyze and generate recommendation
        score = 0
        signals = []

        # Technical Analysis Signals
        # 1. Price vs Moving Averages
        if indicators['above_sma_50']:
            score += 1
            signals.append("Price above 50-day MA (Bullish)")
        else:
            score -= 1
            signals.append("Price below 50-day MA (Bearish)")

        if indicators['above_sma_200']:
            score += 1
            signals.append("Price above 200-day MA (Bullish)")
        else:
            score -= 1
            signals.append("Price below 200-day MA (Bearish)")

        # 2. Golden Cross / Death Cross
        if indicators['golden_cross']:
            score += 2
            signals.append("Golden Cross: 50-day MA > 200-day MA (Strong Bullish)")
        else:
            score -= 1
            signals.append("Death Cross: 50-day MA < 200-day MA (Bearish)")

        # 3. RSI Analysis
        rsi = indicators['rsi']
        if rsi < 30:
            score += 2
            signals.append(f"RSI {rsi:.1f} - Oversold (Strong Buy Signal)")
        elif rsi < 40:
            score += 1
            signals.append(f"RSI {rsi:.1f} - Near Oversold (Buy Signal)")
        elif rsi > 70:
            score -= 2
            signals.append(f"RSI {rsi:.1f} - Overbought (Strong Sell Signal)")
        elif rsi > 60:
            score -= 1
            signals.append(f"RSI {rsi:.1f} - Near Overbought (Sell Signal)")
        else:
            signals.append(f"RSI {rsi:.1f} - Neutral")

        # 4. Recent Price Momentum
        if info['change_percent'] > 2:
            score += 1
            signals.append(f"Strong positive momentum ({info['change_percent']:.2f}%)")
        elif info['change_percent'] < -2:
            score -= 1
            signals.append(f"Strong negative momentum ({info['change_percent']:.2f}%)")

        # 5. Volume Analysis
        if info['volume'] != 'N/A' and info['avg_volume'] != 'N/A':
            volume_ratio = info['volume'] / info['avg_volume']
            if volume_ratio > 1.5:
                signals.append(f"High volume ({volume_ratio:.1f}x average)")
            elif volume_ratio < 0.5:
                signals.append(f"Low volume ({volume_ratio:.1f}x average)")

        # Generate recommendation
        if score >= 4:
            recommendation = "STRONG BUY"
            confidence = "High"
        elif score >= 2:
            recommendation = "BUY"
            confidence = "Medium"
        elif score <= -4:
            recommendation = "STRONG SELL"
            confidence = "High"
        elif score <= -2:
            recommendation = "SELL"
            confidence = "Medium"
        else:
            recommendation = "HOLD"
            confidence = "Low"

        return {
            'ticker': ticker,
            'recommendation': recommendation,
            'confidence': confidence,
            'score': score,
            'signals': signals,
            'info': info,
            'indicators': indicators
        }

    def get_buy_recommendations(self, watchlist: List[str], top_n: int = 5) -> List[Dict]:
        """
        Analyze multiple stocks and return top buy recommendations

        Args:
            watchlist: List of ticker symbols to analyze
            top_n: Number of top recommendations to return

        Returns:
            List of top recommendations sorted by score
        """
        recommendations = []

        for ticker in watchlist:
            analysis = self.analyze_stock(ticker)
            if 'error' not in analysis:
                recommendations.append(analysis)

        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        # Filter for buy recommendations
        buy_recs = [r for r in recommendations if 'BUY' in r['recommendation']]

        return buy_recs[:top_n]

    def analyze_portfolio(self, portfolio: Portfolio) -> Dict:
        """
        Analyze current portfolio and provide sell recommendations

        Args:
            portfolio: Portfolio object

        Returns:
            Dictionary with portfolio analysis and sell recommendations
        """
        positions = portfolio.get_positions()
        if not positions:
            return {
                'message': 'Portfolio is empty',
                'sell_recommendations': []
            }

        # Get current prices
        tickers = list(positions.keys())
        current_data = self.data_fetcher.get_multiple_stocks(tickers)

        # Calculate portfolio metrics
        current_prices = {t: data['current_price'] for t, data in current_data.items()}
        portfolio_value = portfolio.calculate_portfolio_value(current_prices)

        # Analyze each position for sell signals
        sell_recommendations = []
        hold_recommendations = []

        for pos in portfolio_value['positions']:
            ticker = pos['ticker']
            analysis = self.analyze_stock(ticker)

            if 'error' in analysis:
                continue

            # Determine if should sell based on:
            # 1. Strong sell signal from analysis
            # 2. Significant profit (>20%) with overbought signals
            # 3. Significant loss (<-10%) with bearish signals

            should_sell = False
            reason = []

            if analysis['recommendation'] in ['SELL', 'STRONG SELL']:
                should_sell = True
                reason.append(f"Technical analysis: {analysis['recommendation']}")

            if pos['profit_loss_pct'] > 20:
                if analysis['indicators']['rsi'] > 65:
                    should_sell = True
                    reason.append(f"Take profit: +{pos['profit_loss_pct']:.1f}% gain with overbought conditions")

            if pos['profit_loss_pct'] < -10:
                if analysis['score'] < 0:
                    should_sell = True
                    reason.append(f"Cut losses: {pos['profit_loss_pct']:.1f}% loss with bearish signals")

            recommendation_data = {
                'ticker': ticker,
                'shares': pos['shares'],
                'avg_cost': pos['avg_cost'],
                'current_price': pos['current_price'],
                'profit_loss': pos['profit_loss'],
                'profit_loss_pct': pos['profit_loss_pct'],
                'analysis': analysis,
                'reason': ' | '.join(reason) if reason else 'Hold position'
            }

            if should_sell:
                sell_recommendations.append(recommendation_data)
            else:
                hold_recommendations.append(recommendation_data)

        # Sort sell recommendations by urgency (worst performers first for losses, best for profits)
        sell_recommendations.sort(key=lambda x: x['profit_loss_pct'])

        return {
            'portfolio_value': portfolio_value,
            'sell_recommendations': sell_recommendations,
            'hold_recommendations': hold_recommendations
        }

    def screen_stocks(self, criteria: Dict = None) -> List[str]:
        """
        Screen for stocks based on criteria
        Returns a default watchlist of popular stocks

        Args:
            criteria: Screening criteria (future enhancement)

        Returns:
            List of ticker symbols
        """
        # Default watchlist of popular stocks across sectors
        default_watchlist = [
            # Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS',
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV',
            # Consumer
            'WMT', 'HD', 'NKE', 'MCD',
            # Industrial
            'BA', 'CAT', 'GE',
            # Energy
            'XOM', 'CVX',
        ]

        return default_watchlist

"""
Portfolio Management Module
Handles portfolio creation, tracking, and position management
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class Portfolio:
    """Manages stock portfolio with positions and performance tracking"""

    def __init__(self, portfolio_file: str = "portfolio_data.json"):
        self.portfolio_file = portfolio_file
        self.positions = {}
        self.cash = 0.0
        self.load_portfolio()

    def load_portfolio(self):
        """Load portfolio from JSON file"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    self.positions = data.get('positions', {})
                    self.cash = data.get('cash', 0.0)
            except Exception as e:
                print(f"Error loading portfolio: {str(e)}")
                self.positions = {}
                self.cash = 0.0

    def save_portfolio(self):
        """Save portfolio to JSON file"""
        try:
            data = {
                'positions': self.positions,
                'cash': self.cash,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving portfolio: {str(e)}")

    def add_cash(self, amount: float):
        """Add cash to portfolio"""
        if amount > 0:
            self.cash += amount
            self.save_portfolio()
            return True
        return False

    def buy_stock(self, ticker: str, shares: float, price: float) -> bool:
        """
        Buy stock and add to portfolio

        Args:
            ticker: Stock ticker symbol
            shares: Number of shares to buy
            price: Price per share

        Returns:
            True if successful, False otherwise
        """
        total_cost = shares * price
        if total_cost > self.cash:
            print(f"Insufficient funds. Need ${total_cost:.2f}, have ${self.cash:.2f}")
            return False

        ticker = ticker.upper()
        if ticker in self.positions:
            # Update existing position (average cost)
            old_shares = self.positions[ticker]['shares']
            old_cost = self.positions[ticker]['avg_cost']
            new_shares = old_shares + shares
            new_avg_cost = ((old_shares * old_cost) + (shares * price)) / new_shares

            self.positions[ticker]['shares'] = new_shares
            self.positions[ticker]['avg_cost'] = new_avg_cost
            self.positions[ticker]['last_updated'] = datetime.now().isoformat()
        else:
            # New position
            self.positions[ticker] = {
                'shares': shares,
                'avg_cost': price,
                'purchase_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }

        self.cash -= total_cost
        self.save_portfolio()
        print(f"Bought {shares} shares of {ticker} at ${price:.2f}")
        return True

    def sell_stock(self, ticker: str, shares: float, price: float) -> bool:
        """
        Sell stock from portfolio

        Args:
            ticker: Stock ticker symbol
            shares: Number of shares to sell
            price: Price per share

        Returns:
            True if successful, False otherwise
        """
        ticker = ticker.upper()
        if ticker not in self.positions:
            print(f"No position in {ticker}")
            return False

        current_shares = self.positions[ticker]['shares']
        if shares > current_shares:
            print(f"Cannot sell {shares} shares. Only have {current_shares}")
            return False

        # Calculate profit/loss
        avg_cost = self.positions[ticker]['avg_cost']
        profit_loss = (price - avg_cost) * shares
        total_proceeds = shares * price

        # Update position
        if shares == current_shares:
            # Selling entire position
            del self.positions[ticker]
        else:
            # Partial sale
            self.positions[ticker]['shares'] = current_shares - shares
            self.positions[ticker]['last_updated'] = datetime.now().isoformat()

        self.cash += total_proceeds
        self.save_portfolio()
        print(f"Sold {shares} shares of {ticker} at ${price:.2f}")
        print(f"Profit/Loss: ${profit_loss:.2f} ({(profit_loss/avg_cost/shares)*100:.2f}%)")
        return True

    def get_positions(self) -> Dict:
        """Get all current positions"""
        return self.positions.copy()

    def get_position(self, ticker: str) -> Optional[Dict]:
        """Get specific position"""
        return self.positions.get(ticker.upper())

    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        """
        Calculate total portfolio value with current prices

        Args:
            current_prices: Dictionary mapping tickers to current prices

        Returns:
            Dictionary with portfolio metrics
        """
        total_invested = 0.0
        current_value = 0.0
        positions_detail = []

        for ticker, position in self.positions.items():
            shares = position['shares']
            avg_cost = position['avg_cost']
            invested = shares * avg_cost

            current_price = current_prices.get(ticker, avg_cost)
            value = shares * current_price
            profit_loss = value - invested
            profit_loss_pct = (profit_loss / invested * 100) if invested > 0 else 0

            total_invested += invested
            current_value += value

            positions_detail.append({
                'ticker': ticker,
                'shares': shares,
                'avg_cost': avg_cost,
                'current_price': current_price,
                'invested': invested,
                'current_value': value,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct
            })

        total_value = current_value + self.cash
        total_profit_loss = current_value - total_invested

        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'cash': self.cash,
            'total_value': total_value,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_pct': (total_profit_loss / total_invested * 100) if total_invested > 0 else 0,
            'positions': positions_detail
        }

    def is_empty(self) -> bool:
        """Check if portfolio has no positions"""
        return len(self.positions) == 0

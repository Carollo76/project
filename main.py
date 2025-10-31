#!/usr/bin/env python3
"""
Stock Analyzer Tool - Main CLI Interface
Provides buy/sell recommendations for stocks and portfolio management
"""

import sys
from colorama import Fore, Style, init
from tabulate import tabulate
from stock_analyzer import StockAnalyzer
from portfolio import Portfolio
from data_fetcher import StockDataFetcher

# Initialize colorama
init(autoreset=True)


class StockAnalyzerCLI:
    """Command-line interface for stock analysis tool"""

    def __init__(self):
        self.analyzer = StockAnalyzer()
        self.portfolio = Portfolio()
        self.data_fetcher = StockDataFetcher()

    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{text.center(80)}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

    def print_recommendation(self, rec: str) -> str:
        """Color code recommendation"""
        if 'STRONG BUY' in rec:
            return f"{Fore.GREEN}{Style.BRIGHT}{rec}{Style.RESET_ALL}"
        elif 'BUY' in rec:
            return f"{Fore.GREEN}{rec}{Style.RESET_ALL}"
        elif 'STRONG SELL' in rec:
            return f"{Fore.RED}{Style.BRIGHT}{rec}{Style.RESET_ALL}"
        elif 'SELL' in rec:
            return f"{Fore.RED}{rec}{Style.RESET_ALL}"
        else:
            return f"{Fore.YELLOW}{rec}{Style.RESET_ALL}"

    def format_price(self, value: float) -> str:
        """Format price with color"""
        if value > 0:
            return f"{Fore.GREEN}${value:,.2f}{Style.RESET_ALL}"
        elif value < 0:
            return f"{Fore.RED}${value:,.2f}{Style.RESET_ALL}"
        else:
            return f"${value:,.2f}"

    def format_percent(self, value: float) -> str:
        """Format percentage with color"""
        if value > 0:
            return f"{Fore.GREEN}+{value:.2f}%{Style.RESET_ALL}"
        elif value < 0:
            return f"{Fore.RED}{value:.2f}%{Style.RESET_ALL}"
        else:
            return f"{value:.2f}%"

    def analyze_single_stock(self, ticker: str):
        """Analyze and display single stock analysis"""
        self.print_header(f"Analyzing {ticker.upper()}")

        analysis = self.analyzer.analyze_stock(ticker)

        if 'error' in analysis:
            print(f"{Fore.RED}Error: {analysis['error']}{Style.RESET_ALL}")
            return

        info = analysis['info']
        indicators = analysis['indicators']

        # Stock info table
        stock_data = [
            ["Ticker", info['ticker']],
            ["Name", info['name']],
            ["Current Price", f"${info['current_price']:.2f}"],
            ["Previous Close", f"${info['previous_close']:.2f}"],
            ["Change", self.format_percent(info['change_percent'])],
            ["Sector", info['sector']],
            ["P/E Ratio", f"{info['pe_ratio']:.2f}" if info['pe_ratio'] != 'N/A' else 'N/A'],
        ]

        print(f"{Fore.YELLOW}Stock Information:{Style.RESET_ALL}")
        print(tabulate(stock_data, tablefmt="simple"))

        # Technical indicators
        print(f"\n{Fore.YELLOW}Technical Indicators:{Style.RESET_ALL}")
        tech_data = [
            ["50-Day MA", f"${indicators['sma_50']:.2f}"],
            ["200-Day MA", f"${indicators['sma_200']:.2f}"],
            ["RSI (14)", f"{indicators['rsi']:.2f}"],
            ["Golden Cross", "Yes" if indicators['golden_cross'] else "No"],
        ]
        print(tabulate(tech_data, tablefmt="simple"))

        # Signals
        print(f"\n{Fore.YELLOW}Analysis Signals:{Style.RESET_ALL}")
        for signal in analysis['signals']:
            print(f"  • {signal}")

        # Recommendation
        print(f"\n{Fore.YELLOW}Recommendation:{Style.RESET_ALL}")
        print(f"  {self.print_recommendation(analysis['recommendation'])} (Confidence: {analysis['confidence']}, Score: {analysis['score']})")

    def show_buy_recommendations(self, custom_tickers: list = None):
        """Display buy recommendations"""
        self.print_header("Stock Buy Recommendations")

        if custom_tickers:
            watchlist = custom_tickers
            print(f"Analyzing custom watchlist: {', '.join(watchlist)}\n")
        else:
            watchlist = self.analyzer.screen_stocks()
            print(f"Analyzing {len(watchlist)} stocks from default watchlist...\n")

        recommendations = self.analyzer.get_buy_recommendations(watchlist, top_n=10)

        if not recommendations:
            print(f"{Fore.YELLOW}No buy recommendations found at this time.{Style.RESET_ALL}")
            return

        # Create table
        table_data = []
        for rec in recommendations:
            info = rec['info']
            table_data.append([
                info['ticker'],
                info['name'][:30],
                f"${info['current_price']:.2f}",
                self.format_percent(info['change_percent']),
                f"{rec['indicators']['rsi']:.1f}",
                self.print_recommendation(rec['recommendation']),
                rec['score'],
                rec['confidence']
            ])

        headers = ["Ticker", "Name", "Price", "Change", "RSI", "Recommendation", "Score", "Confidence"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        print(f"\n{Fore.CYAN}💡 Tip: Use 'analyze <ticker>' for detailed analysis of any stock{Style.RESET_ALL}")

    def show_sell_recommendations(self):
        """Display sell recommendations for portfolio"""
        self.print_header("Portfolio Sell Recommendations")

        if self.portfolio.is_empty():
            print(f"{Fore.YELLOW}Your portfolio is empty. Add positions first!{Style.RESET_ALL}")
            print(f"\nUse commands:")
            print(f"  • 'buy <ticker> <shares>' to add positions")
            print(f"  • 'cash <amount>' to add cash to your account")
            return

        analysis = self.analyzer.analyze_portfolio(self.portfolio)

        # Show portfolio summary
        pv = analysis['portfolio_value']
        print(f"{Fore.YELLOW}Portfolio Summary:{Style.RESET_ALL}")
        summary_data = [
            ["Total Invested", f"${pv['total_invested']:,.2f}"],
            ["Current Value", f"${pv['current_value']:,.2f}"],
            ["Cash", f"${pv['cash']:,.2f}"],
            ["Total Portfolio Value", f"${pv['total_value']:,.2f}"],
            ["Total P/L", self.format_price(pv['total_profit_loss'])],
            ["Total P/L %", self.format_percent(pv['total_profit_loss_pct'])],
        ]
        print(tabulate(summary_data, tablefmt="simple"))

        # Sell recommendations
        if analysis['sell_recommendations']:
            print(f"\n{Fore.RED}{Style.BRIGHT}⚠️  SELL RECOMMENDATIONS:{Style.RESET_ALL}")
            sell_data = []
            for rec in analysis['sell_recommendations']:
                sell_data.append([
                    rec['ticker'],
                    f"{rec['shares']:.2f}",
                    f"${rec['avg_cost']:.2f}",
                    f"${rec['current_price']:.2f}",
                    self.format_price(rec['profit_loss']),
                    self.format_percent(rec['profit_loss_pct']),
                    self.print_recommendation(rec['analysis']['recommendation']),
                    rec['reason'][:50]
                ])
            headers = ["Ticker", "Shares", "Avg Cost", "Current", "P/L", "P/L %", "Signal", "Reason"]
            print(tabulate(sell_data, headers=headers, tablefmt="grid"))
        else:
            print(f"\n{Fore.GREEN}✓ No sell signals detected. All positions look good!{Style.RESET_ALL}")

        # Hold recommendations
        if analysis['hold_recommendations']:
            print(f"\n{Fore.GREEN}✓ POSITIONS TO HOLD:{Style.RESET_ALL}")
            hold_data = []
            for rec in analysis['hold_recommendations']:
                hold_data.append([
                    rec['ticker'],
                    f"{rec['shares']:.2f}",
                    f"${rec['current_price']:.2f}",
                    self.format_price(rec['profit_loss']),
                    self.format_percent(rec['profit_loss_pct']),
                    self.print_recommendation(rec['analysis']['recommendation'])
                ])
            headers = ["Ticker", "Shares", "Current Price", "P/L", "P/L %", "Signal"]
            print(tabulate(hold_data, headers=headers, tablefmt="grid"))

    def show_portfolio(self):
        """Display current portfolio"""
        self.print_header("Current Portfolio")

        if self.portfolio.is_empty():
            print(f"{Fore.YELLOW}Your portfolio is empty.{Style.RESET_ALL}")
            print(f"\nAvailable cash: ${self.portfolio.cash:,.2f}")
            return

        # Get current prices
        positions = self.portfolio.get_positions()
        tickers = list(positions.keys())
        current_data = self.data_fetcher.get_multiple_stocks(tickers)
        current_prices = {t: data['current_price'] for t, data in current_data.items()}

        # Calculate portfolio value
        pv = self.portfolio.calculate_portfolio_value(current_prices)

        # Display positions
        table_data = []
        for pos in pv['positions']:
            table_data.append([
                pos['ticker'],
                f"{pos['shares']:.2f}",
                f"${pos['avg_cost']:.2f}",
                f"${pos['current_price']:.2f}",
                f"${pos['invested']:,.2f}",
                f"${pos['current_value']:,.2f}",
                self.format_price(pos['profit_loss']),
                self.format_percent(pos['profit_loss_pct'])
            ])

        headers = ["Ticker", "Shares", "Avg Cost", "Current", "Invested", "Value", "P/L", "P/L %"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Summary
        print(f"\n{Fore.YELLOW}Summary:{Style.RESET_ALL}")
        summary_data = [
            ["Cash Available", f"${pv['cash']:,.2f}"],
            ["Total Invested", f"${pv['total_invested']:,.2f}"],
            ["Current Value", f"${pv['current_value']:,.2f}"],
            ["Total Portfolio", f"${pv['total_value']:,.2f}"],
            ["Total P/L", self.format_price(pv['total_profit_loss'])],
            ["Total Return", self.format_percent(pv['total_profit_loss_pct'])],
        ]
        print(tabulate(summary_data, tablefmt="simple"))

    def buy_stock_interactive(self, ticker: str = None, shares: float = None):
        """Buy stock with current price"""
        if not ticker:
            ticker = input("Enter ticker symbol: ").strip().upper()

        # Get current price
        info = self.data_fetcher.get_stock_info(ticker)
        if not info:
            print(f"{Fore.RED}Unable to fetch data for {ticker}{Style.RESET_ALL}")
            return

        print(f"\n{info['name']} ({ticker})")
        print(f"Current Price: ${info['current_price']:.2f}")
        print(f"Available Cash: ${self.portfolio.cash:,.2f}")

        if not shares:
            shares_input = input(f"\nEnter number of shares to buy: ").strip()
            try:
                shares = float(shares_input)
            except ValueError:
                print(f"{Fore.RED}Invalid share amount{Style.RESET_ALL}")
                return

        total_cost = shares * info['current_price']
        print(f"\nTotal Cost: ${total_cost:,.2f}")

        confirm = input(f"Confirm purchase? (y/n): ").strip().lower()
        if confirm == 'y':
            self.portfolio.buy_stock(ticker, shares, info['current_price'])

    def sell_stock_interactive(self, ticker: str = None, shares: float = None):
        """Sell stock at current price"""
        if not ticker:
            ticker = input("Enter ticker symbol: ").strip().upper()

        position = self.portfolio.get_position(ticker)
        if not position:
            print(f"{Fore.RED}No position in {ticker}{Style.RESET_ALL}")
            return

        # Get current price
        info = self.data_fetcher.get_stock_info(ticker)
        if not info:
            print(f"{Fore.RED}Unable to fetch data for {ticker}{Style.RESET_ALL}")
            return

        print(f"\n{info['name']} ({ticker})")
        print(f"Shares Owned: {position['shares']:.2f}")
        print(f"Average Cost: ${position['avg_cost']:.2f}")
        print(f"Current Price: ${info['current_price']:.2f}")

        profit_loss = (info['current_price'] - position['avg_cost']) * position['shares']
        print(f"Total P/L: {self.format_price(profit_loss)}")

        if not shares:
            shares_input = input(f"\nEnter number of shares to sell (or 'all'): ").strip()
            if shares_input.lower() == 'all':
                shares = position['shares']
            else:
                try:
                    shares = float(shares_input)
                except ValueError:
                    print(f"{Fore.RED}Invalid share amount{Style.RESET_ALL}")
                    return

        total_proceeds = shares * info['current_price']
        print(f"\nTotal Proceeds: ${total_proceeds:,.2f}")

        confirm = input(f"Confirm sale? (y/n): ").strip().lower()
        if confirm == 'y':
            self.portfolio.sell_stock(ticker, shares, info['current_price'])

    def show_help(self):
        """Display help menu"""
        self.print_header("Stock Analyzer Tool - Help")

        help_text = f"""
{Fore.YELLOW}ANALYSIS COMMANDS:{Style.RESET_ALL}
  buy-recs [ticker1,ticker2,...]  Show buy recommendations (optional: custom watchlist)
  sell-recs                        Show sell recommendations for your portfolio
  analyze <ticker>                 Detailed analysis of a specific stock

{Fore.YELLOW}PORTFOLIO COMMANDS:{Style.RESET_ALL}
  portfolio                        View current portfolio
  buy <ticker> [shares]           Buy stock (interactive if shares not provided)
  sell <ticker> [shares]          Sell stock (interactive if shares not provided)
  cash <amount>                    Add cash to portfolio

{Fore.YELLOW}OTHER COMMANDS:{Style.RESET_ALL}
  help                             Show this help menu
  quit / exit                      Exit the program

{Fore.CYAN}EXAMPLES:{Style.RESET_ALL}
  buy-recs                         # Get top 10 buy recommendations
  buy-recs AAPL,MSFT,GOOGL        # Analyze specific stocks
  analyze TSLA                     # Detailed analysis of Tesla
  buy AAPL 10                      # Buy 10 shares of Apple
  sell AAPL 5                      # Sell 5 shares of Apple
  cash 10000                       # Add $10,000 to portfolio
        """
        print(help_text)

    def run(self):
        """Main CLI loop"""
        self.print_header("Stock Analyzer Tool")
        print(f"{Fore.GREEN}Welcome to Stock Analyzer!{Style.RESET_ALL}")
        print(f"Type 'help' for available commands or 'quit' to exit.\n")

        while True:
            try:
                command = input(f"{Fore.CYAN}stock-analyzer> {Style.RESET_ALL}").strip()

                if not command:
                    continue

                parts = command.split()
                cmd = parts[0].lower()

                if cmd in ['quit', 'exit']:
                    print(f"\n{Fore.GREEN}Thank you for using Stock Analyzer!{Style.RESET_ALL}\n")
                    break

                elif cmd == 'help':
                    self.show_help()

                elif cmd == 'buy-recs':
                    if len(parts) > 1:
                        tickers = parts[1].split(',')
                        self.show_buy_recommendations(tickers)
                    else:
                        self.show_buy_recommendations()

                elif cmd == 'sell-recs':
                    self.show_sell_recommendations()

                elif cmd == 'analyze':
                    if len(parts) < 2:
                        print(f"{Fore.RED}Usage: analyze <ticker>{Style.RESET_ALL}")
                    else:
                        self.analyze_single_stock(parts[1])

                elif cmd == 'portfolio':
                    self.show_portfolio()

                elif cmd == 'buy':
                    ticker = parts[1] if len(parts) > 1 else None
                    shares = float(parts[2]) if len(parts) > 2 else None
                    self.buy_stock_interactive(ticker, shares)

                elif cmd == 'sell':
                    ticker = parts[1] if len(parts) > 1 else None
                    shares = float(parts[2]) if len(parts) > 2 else None
                    self.sell_stock_interactive(ticker, shares)

                elif cmd == 'cash':
                    if len(parts) < 2:
                        print(f"{Fore.RED}Usage: cash <amount>{Style.RESET_ALL}")
                    else:
                        try:
                            amount = float(parts[1])
                            self.portfolio.add_cash(amount)
                            print(f"{Fore.GREEN}Added ${amount:,.2f} to portfolio{Style.RESET_ALL}")
                            print(f"New cash balance: ${self.portfolio.cash:,.2f}")
                        except ValueError:
                            print(f"{Fore.RED}Invalid amount{Style.RESET_ALL}")

                else:
                    print(f"{Fore.RED}Unknown command: {cmd}{Style.RESET_ALL}")
                    print(f"Type 'help' for available commands")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.GREEN}Thank you for using Stock Analyzer!{Style.RESET_ALL}\n")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")


def main():
    """Entry point"""
    cli = StockAnalyzerCLI()
    cli.run()


if __name__ == "__main__":
    main()

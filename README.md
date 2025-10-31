# Stock Analyzer Tool

A comprehensive Python-based stock analysis tool that provides intelligent buy and sell recommendations using technical analysis, moving averages, RSI indicators, and portfolio management.

## Features

### 📊 Stock Analysis
- **Technical Analysis**: RSI, Moving Averages (50-day, 200-day), Golden Cross detection
- **Buy Recommendations**: Analyzes stocks and recommends top buying opportunities
- **Sell Recommendations**: Monitors portfolio positions and suggests when to sell
- **Detailed Stock Analysis**: In-depth analysis of individual stocks with signals

### 💼 Portfolio Management
- **Position Tracking**: Track multiple stock positions with average cost basis
- **Profit/Loss Calculation**: Real-time P/L for each position and overall portfolio
- **Cash Management**: Maintain cash balance for trading
- **Persistent Storage**: Portfolio data saved in JSON format

### 🎯 Recommendation Engine
The tool analyzes stocks based on multiple factors:
- Price vs 50-day and 200-day moving averages
- RSI (Relative Strength Index) - oversold/overbought conditions
- Golden Cross / Death Cross patterns
- Price momentum and volume analysis
- Comprehensive scoring system for confidence levels

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository:
```bash
cd project
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install yfinance pandas numpy requests colorama tabulate
```

## Usage

### Starting the Tool

Run the main script:
```bash
python main.py
```

Or make it executable:
```bash
chmod +x main.py
./main.py
```

### Available Commands

#### Analysis Commands

**Get Buy Recommendations**
```bash
buy-recs                          # Analyze 25+ popular stocks and show top 10 buys
buy-recs AAPL,MSFT,GOOGL,TSLA    # Analyze specific stocks
```

**Get Sell Recommendations**
```bash
sell-recs                         # Analyze your portfolio and suggest sells
```

**Analyze Individual Stock**
```bash
analyze AAPL                      # Detailed analysis of Apple stock
```

#### Portfolio Commands

**View Portfolio**
```bash
portfolio                         # View all positions and portfolio summary
```

**Add Cash**
```bash
cash 10000                        # Add $10,000 to your portfolio
```

**Buy Stock**
```bash
buy AAPL 10                       # Buy 10 shares of Apple at current price
buy MSFT                          # Interactive mode - prompts for shares
```

**Sell Stock**
```bash
sell AAPL 5                       # Sell 5 shares of Apple
sell MSFT all                     # Sell all Microsoft shares
sell GOOGL                        # Interactive mode
```

#### Other Commands
```bash
help                              # Show help menu
quit / exit                       # Exit the program
```

## Example Workflow

### 1. Add Cash to Portfolio
```bash
stock-analyzer> cash 50000
Added $50,000.00 to portfolio
New cash balance: $50,000.00
```

### 2. Get Buy Recommendations
```bash
stock-analyzer> buy-recs
================================================================================
                        Stock Buy Recommendations
================================================================================

Analyzing 25 stocks from default watchlist...

╒══════════╤════════════════════╤═════════╤══════════╤═══════╤═══════════════╤═════════╤══════════════╕
│ Ticker   │ Name               │ Price   │ Change   │   RSI │ Recommendation│  Score  │ Confidence   │
╞══════════╪════════════════════╪═════════╪══════════╪═══════╪═══════════════╪═════════╪══════════════╡
│ NVDA     │ NVIDIA Corporation │ $450.25 │ +2.5%    │  35.2 │ STRONG BUY    │    6    │ High         │
│ AAPL     │ Apple Inc.         │ $175.50 │ +1.2%    │  42.1 │ BUY           │    3    │ Medium       │
╘══════════╧════════════════════╧═════════╧══════════╧═══════╧═══════════════╧═════════╧══════════════╛
```

### 3. Analyze Specific Stock
```bash
stock-analyzer> analyze NVDA
```

### 4. Buy a Stock
```bash
stock-analyzer> buy NVDA 20
Bought 20 shares of NVDA at $450.25
```

### 5. View Portfolio
```bash
stock-analyzer> portfolio
```

### 6. Get Sell Recommendations
```bash
stock-analyzer> sell-recs
```

### 7. Sell a Stock
```bash
stock-analyzer> sell NVDA 10
Sold 10 shares of NVDA at $475.80
Profit/Loss: $510.00 (+5.66%)
```

## How the Recommendation System Works

### Buy Signals (Positive Score)
- ✅ Price above 50-day MA (+1)
- ✅ Price above 200-day MA (+1)
- ✅ Golden Cross: 50-day MA > 200-day MA (+2)
- ✅ RSI < 30 (Oversold) (+2)
- ✅ RSI < 40 (Near Oversold) (+1)
- ✅ Strong positive momentum (+1)

### Sell Signals (Negative Score)
- ⚠️ Price below 50-day MA (-1)
- ⚠️ Price below 200-day MA (-1)
- ⚠️ Death Cross: 50-day MA < 200-day MA (-1)
- ⚠️ RSI > 70 (Overbought) (-2)
- ⚠️ RSI > 60 (Near Overbought) (-1)
- ⚠️ Strong negative momentum (-1)

### Recommendation Levels
- **STRONG BUY**: Score ≥ 4 (High Confidence)
- **BUY**: Score ≥ 2 (Medium Confidence)
- **HOLD**: Score between -1 and 1 (Low Confidence)
- **SELL**: Score ≤ -2 (Medium Confidence)
- **STRONG SELL**: Score ≤ -4 (High Confidence)

### Portfolio Sell Triggers
The tool recommends selling positions when:
1. Technical analysis shows SELL or STRONG SELL signal
2. Position has >20% profit with overbought RSI (take profit)
3. Position has <-10% loss with bearish signals (cut losses)

## Technical Details

### Data Source
- **yfinance**: Real-time and historical stock data from Yahoo Finance
- Data includes: price, volume, moving averages, P/E ratios, market cap, etc.

### Technical Indicators
- **SMA (Simple Moving Average)**: 50-day and 200-day
- **RSI (Relative Strength Index)**: 14-period RSI
- **Golden/Death Cross**: Crossover of 50-day and 200-day MAs
- **Volume Analysis**: Comparison with average volume

### Portfolio Storage
- Portfolio data stored in `portfolio_data.json`
- Includes: positions, shares, average cost, timestamps
- Automatically saved after each transaction

## Project Structure

```
project/
├── main.py              # CLI interface and main entry point
├── stock_analyzer.py    # Analysis engine and recommendation logic
├── portfolio.py         # Portfolio management system
├── data_fetcher.py      # Stock data fetching via yfinance
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── portfolio_data.json # Portfolio data (created automatically)
```

## Important Notes

### ⚠️ Disclaimer
This tool is for educational and informational purposes only. It is NOT financial advice. Always:
- Do your own research before investing
- Consider your risk tolerance
- Consult with a financial advisor
- Never invest money you can't afford to lose
- Past performance doesn't guarantee future results

### Data Accuracy
- Stock data is fetched in real-time from Yahoo Finance
- Market data may have slight delays
- Some stocks may not have complete data available

### Best Practices
- Start with a reasonable cash amount for your risk level
- Diversify your portfolio across sectors
- Review both buy and sell recommendations regularly
- Use detailed analysis before making decisions
- Monitor your portfolio performance

## Troubleshooting

### "Unable to fetch data for ticker"
- Check that the ticker symbol is valid
- Ensure you have internet connection
- Some stocks may not be available on Yahoo Finance

### "Insufficient funds"
- Use `cash <amount>` to add more cash
- Check your available balance with `portfolio`

### Module Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

## Future Enhancements

Potential features for future versions:
- [ ] More technical indicators (MACD, Bollinger Bands, etc.)
- [ ] Fundamental analysis (earnings, revenue growth, etc.)
- [ ] Stock screening with custom criteria
- [ ] Backtesting capabilities
- [ ] Price alerts and notifications
- [ ] Export reports to PDF/Excel
- [ ] Integration with real brokers (paper trading)
- [ ] Machine learning-based predictions

## Contributing

Feel free to fork this project and submit pull requests with improvements!

## License

This project is open source and available for educational purposes.

---

**Happy Trading! 📈**

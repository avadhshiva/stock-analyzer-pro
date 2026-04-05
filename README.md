# Stock Analyzer Pro

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Charts-3f4f75?logo=plotly&logoColor=white)
![Yahoo Finance](https://img.shields.io/badge/Data-Yahoo%20Finance-5f01d1)
![Status](https://img.shields.io/badge/Status-Active-success)

A Streamlit-based stock analysis dashboard inspired by Zerodha, Groww, and Paytm Money.

This project helps users search stocks, inspect price action across multiple timeframes, review technical signals, and simulate paper trades with simple risk controls.

## Why This Project

Retail traders and investors often want a simple place to:

- search stocks quickly
- switch between intraday and higher timeframes
- understand technical indicators without opening multiple tools
- experiment with trade setups without risking capital

Stock Analyzer Pro is designed as a lightweight dashboard that brings those workflows into one Streamlit app.

## What This App Does

- Search stocks using ticker symbols or company names
- Fetch market data from Yahoo Finance
- Visualize candlestick charts with popular indicators
- Generate simple BUY, SELL, or HOLD signals
- Support multiple chart timeframes from intraday to monthly
- Simulate paper trades with entry, stop loss, target, and quantity
- Provide a lightweight trade dashboard with PnL-style tracking

## Features

- Smart stock search with ticker and company-name matching
- Technical indicators such as RSI, EMA, and VWAP
- BUY, SELL, and HOLD signal generation
- Multiple chart timeframes from intraday to monthly
- Paper trading with basic risk management
- Trade dashboard with simple PnL tracking

## Demo And Deployment

- Local app: run with `streamlit run app.py`
- GitHub repo: [stock-analyzer-pro](https://github.com/avadhshiva/stock-analyzer-pro)
- Deploy option: Streamlit Community Cloud, Render, or any Python-friendly hosting platform

If you deploy this app publicly, you can add the live link here later.

## Supported Timeframes

- `1m`
- `3m`
- `5m`
- `10m`
- `15m`
- `30m`
- `1h`
- `4h`
- `8h`
- `1D`
- `2D`
- `5D`
- `7D`
- `1W`
- `1M`
- `2M`
- `3M`

## Tech Stack

- `Python`
- `Streamlit`
- `pandas`
- `yfinance`
- `plotly`
- `requests`

## Screenshots

### Homepage
![Homepage](screenshots/homepage.png)

### Search And Match Suggestions
![Search](screenshots/search.png)

### Analysis Dashboard
![Analysis](screenshots/analysis.png)

### Timeframe Selection
![Timeframe](screenshots/timeframe.png)

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal, usually:

```bash
http://localhost:8501
```

## How To Use

1. Enter a stock name or ticker in the search box.
2. Pick the correct stock if multiple matches are shown.
3. Choose a timeframe based on your trading style.
4. Review the chart, indicators, and signal output.
5. Use the paper trade section to simulate a setup.

## Current Indicators

- `EMA 9`
- `EMA 21`
- `RSI`
- `VWAP`

## Folder Structure

```text
.
|-- app.py
|-- indicators.py
|-- trade_engine.py
|-- utils.py
|-- requirements.txt
|-- trades.json
`-- screenshots/
```

## Roadmap

- Better autocomplete and smarter stock suggestions
- Richer score explanation showing how each signal is derived
- Improved UI inspired by modern brokerage apps
- Technical plus fundamental reasoning in one screen
- Better error handling for missing symbols and unavailable price data
- More advanced AI recommendations for intraday, swing, and long-term investing

## Notes

- Market data availability depends on Yahoo Finance.
- Some symbols may require exchange suffixes such as `.NS`.
- Intraday data availability can vary by symbol and exchange.

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import pandas as pd

from indicators import calculate_indicators
from trade_engine import (
    create_trade,
    load_trades,
    calculate_pnl,
    update_trade_status,
    save_trades
)

st.set_page_config(page_title="Stock Analyzer Pro", layout="wide")

st.title("📊 Stock Analyzer Pro")

# ---------- SEARCH ----------
@st.cache_data(ttl=3600)
def search_stocks(query):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"q": query, "quotesCount": 5, "newsCount": 0}

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()

        results = []
        for item in data.get("quotes", []):
            symbol = item.get("symbol")
            name = item.get("shortname") or item.get("longname")

            if symbol and name:
                results.append((name, symbol))

        return results
    except:
        return []


# ---------- FETCH ----------
def fetch_data(ticker):
    return yf.download(ticker, period="60d", interval="1d", progress=False)


# ---------- ANALYSIS ----------
def analyze_stock(ticker):
    data = fetch_data(ticker)

    if data is None or data.empty or len(data) < 30:
        return None

    if hasattr(data.columns, "levels"):
        data.columns = data.columns.get_level_values(0)

    data = calculate_indicators(data)

    close = float(data['Close'].iloc[-1])
    prev_close = float(data['Close'].iloc[-2])
    ma20 = float(data['MA20'].iloc[-1])
    rsi = float(data['RSI'].iloc[-1])
    ema9 = float(data['EMA9'].iloc[-1])
    ema21 = float(data['EMA21'].iloc[-1])
    vwap = float(data['VWAP'].iloc[-1])

    momentum = ((close - prev_close) / prev_close) * 100

    avg_vol = data['Volume'].rolling(20).mean().iloc[-1]
    volume = data['Volume'].iloc[-1]
    vol_signal = "High" if volume > avg_vol else "Normal"

    score = 0
    if close > ma20: score += 1
    if rsi < 55: score += 1
    if ema9 > ema21: score += 1
    if close > vwap: score += 1

    if score >= 3:
        signal, color = "BUY", "green"
    elif score <= 1:
        signal, color = "SELL", "red"
    else:
        signal, color = "HOLD", "orange"

    return {
        "signal": signal,
        "color": color,
        "score": score,
        "momentum": round(momentum, 2),
        "volume": vol_signal,
        "rsi": round(rsi, 2),
        "data": data
    }


# ---------- CHART ----------
def plot_chart(data):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    ))

    fig.add_trace(go.Scatter(x=data.index, y=data['EMA9'], name='EMA9'))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA21'], name='EMA21'))
    fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], name='VWAP'))

    fig.update_layout(
        template="plotly_dark",
        height=600,
        xaxis_rangeslider_visible=False
    )

    return fig


# ---------- UI ----------
query = st.text_input("🔍 Search Stock (Apple, Tesla, NVDA...)")

selected_symbol = None

if query:
    suggestions = search_stocks(query)

    if suggestions:
        options = [f"{name} ({symbol})" for name, symbol in suggestions]
        selected = st.selectbox("Select Stock", options)

        if selected:
            selected_symbol = selected.split("(")[-1].replace(")", "")
    else:
        st.warning("No suggestions found")

# fallback (manual ticker)
if not selected_symbol and query:
    if len(query.strip()) <= 5:
        selected_symbol = query.strip().upper()


# ---------- AUTO ANALYSIS ----------
if selected_symbol:
    result = analyze_stock(selected_symbol)

    if result:
        st.markdown(
            f"## {selected_symbol} → <span style='color:{result['color']}'>{result['signal']}</span>",
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Score", result["score"])
        col2.metric("Momentum %", result["momentum"])
        col3.metric("RSI", result["rsi"])
        col4.metric("Volume", result["volume"])

        st.plotly_chart(plot_chart(result["data"]), use_container_width=True)

        # ---------- PAPER TRADE ----------
        st.subheader("📈 Paper Trading")

        price = float(result["data"]['Close'].iloc[-1])

        if st.button("Execute Paper Trade"):
            trade = create_trade(selected_symbol, result["signal"], price)

            st.success(f"""
Ticker: {trade['ticker']}
Entry: {trade['entry']}
Stop Loss: {trade['stop_loss']}
Target: {trade['target']}
Quantity: {trade['quantity']}
""")


# ---------- DASHBOARD ----------
st.subheader("📊 Trade Dashboard")

trades = load_trades()

if trades:
    total_pnl = 0
    closed_trades = []
    equity_curve = []

    for trade in trades:
        try:
            data = yf.download(trade["ticker"], period="1d", interval="1d", progress=False)
            current = float(data['Close'].iloc[-1])

            # AUTO CLOSE
            trade = update_trade_status(trade, current)

            if trade["status"] == "CLOSED":
                pnl = trade["pnl"]
                closed_trades.append(trade)
            else:
                pnl = calculate_pnl(trade, current)

            total_pnl += pnl
            equity_curve.append(total_pnl)

            st.write(f"""
{trade['ticker']} | {trade['signal']} | Status: {trade['status']}
Entry: {trade['entry']} | Current: {current}
PnL: {round(pnl,2)}
""")

        except:
            continue

    # SAVE UPDATED TRADES
    save_trades(trades)

    # METRICS
    st.metric("Total PnL", round(total_pnl, 2))

    wins = [t for t in closed_trades if t["pnl"] > 0]
    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0

    st.metric("Win Rate %", round(win_rate, 2))

    # EQUITY CURVE
    if equity_curve:
        st.subheader("📈 Equity Curve")
        df = pd.DataFrame({"Equity": equity_curve})
        st.line_chart(df)

else:
    st.info("No trades yet")
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

TIMEFRAME_CONFIG = {
    "1m": {"period": "7d", "interval": "1m", "resample": None, "intraday": True},
    "3m": {"period": "7d", "interval": "1m", "resample": "3min", "intraday": True},
    "5m": {"period": "30d", "interval": "5m", "resample": None, "intraday": True},
    "10m": {"period": "30d", "interval": "5m", "resample": "10min", "intraday": True},
    "15m": {"period": "30d", "interval": "15m", "resample": None, "intraday": True},
    "30m": {"period": "60d", "interval": "30m", "resample": None, "intraday": True},
    "1h": {"period": "730d", "interval": "1h", "resample": None, "intraday": True},
    "4h": {"period": "730d", "interval": "4h", "resample": None, "intraday": True},
    "8h": {"period": "730d", "interval": "4h", "resample": "8h", "intraday": True},
    "1D": {"period": "2y", "interval": "1d", "resample": None, "intraday": False},
    "2D": {"period": "5y", "interval": "1d", "resample": "2D", "intraday": False},
    "5D": {"period": "5y", "interval": "1d", "resample": "5D", "intraday": False},
    "7D": {"period": "10y", "interval": "1d", "resample": "7D", "intraday": False},
    "1W": {"period": "10y", "interval": "1wk", "resample": None, "intraday": False},
    "1M": {"period": "10y", "interval": "1mo", "resample": None, "intraday": False},
    "2M": {"period": "10y", "interval": "1mo", "resample": "2ME", "intraday": False},
    "3M": {"period": "10y", "interval": "3mo", "resample": None, "intraday": False},
}

# -----------------------------
# 🔍 SMART SEARCH (IMPROVED)
# -----------------------------
COMMON_MAP = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "meta": "META",
    "microsoft": "MSFT",
    "pepsi": "PEP",
    "walmart": "WMT",
    "washington": "WASH",
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc": "HDFCBANK.NS",
}

def resolve_symbol(q):
    q = q.lower().strip().replace("$", "")

    for k, v in COMMON_MAP.items():
        if k in q:
            return v

    q = q.upper()

    # direct
    data = yf.download(q, period="5d", interval="1d", progress=False)
    if not data.empty:
        return q

    # NSE fallback
    data = yf.download(q + ".NS", period="5d", interval="1d", progress=False)
    if not data.empty:
        return q + ".NS"

    return None


# -----------------------------
# 📊 FETCH DATA
# -----------------------------
@st.cache_data(ttl=60)
def fetch_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception:
        return pd.DataFrame()


# -----------------------------
# 📊 INDICATORS
# -----------------------------
def add_indicators(df, intraday=True):
    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA21"] = df["Close"].ewm(span=21).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    if intraday:
        df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

    return df.dropna()


# -----------------------------
# 📊 SIGNAL ENGINE
# -----------------------------
def analyze(df, intraday=True):
    latest = df.iloc[-1]

    if intraday:
        cond = {
            "EMA Bullish": latest["EMA9"] > latest["EMA21"],
            "Above VWAP": latest["Close"] > latest["VWAP"],
            "RSI Safe": 40 < latest["RSI"] < 70,
            "Volume Spike": latest["Volume"] > df["Volume"].rolling(20).mean().iloc[-1],
        }
    else:
        cond = {
            "Trend (MA20)": latest["Close"] > df["Close"].rolling(20).mean().iloc[-1],
            "EMA Bullish": latest["EMA9"] > latest["EMA21"],
            "RSI Healthy": 40 < latest["RSI"] < 70,
        }

    score = sum(cond.values())

    if score >= 3:
        signal = "BUY"
    elif score <= 1:
        signal = "SELL"
    else:
        signal = "HOLD"

    return signal, score, cond


# -----------------------------
# 📊 RESAMPLE (FIXED)
# -----------------------------
def resample_df(df, tf):
    rule_map = {
        "2D": "2D",
        "3D": "3D",
        "5D": "5D",
        "7D": "7D",
        "8h": "8h",
        "10m": "10min",
        "1W": "W",
        "1M": "M",
        "2M": "2ME",
    }

    if tf in rule_map:
        return df.resample(rule_map[tf]).agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }).dropna()

    return df


# -----------------------------
# 📊 CHART
# -----------------------------
def plot_chart(df, intraday):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price"
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df["EMA9"], name="EMA9"))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA21"], name="EMA21"))

    if intraday and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP"))

    fig.update_layout(height=600, template="plotly_dark")
    return fig


# -----------------------------
# 🧠 AI EXPLANATION
# -----------------------------
def ai_explain(signal, cond):
    parts = [f"{k}:{'✔' if v else '✘'}" for k, v in cond.items()]
    return f"{signal} based on -> " + ", ".join(parts)


# -----------------------------
# 🎯 UI
# -----------------------------
st.title("📊 Stock Analyzer Pro")

query = st.text_input("Search Stock")

if query:
    ticker = resolve_symbol(query)

    if not ticker:
        st.error("Stock not found. Try AAPL / NVDA / RELIANCE / PEP / WASH")
        st.stop()

    st.subheader(ticker)
    st.markdown(f"[Yahoo](https://finance.yahoo.com/quote/{ticker})")

    timeframe = st.selectbox("Timeframe", [
        "1m","3m","5m","10m","15m","30m","1h","4h","8h",
        "1D","2D","5D","7D","1W","1M","2M","3M"
    ])

    # -----------------------------
    # TIMEFRAME HANDLING
    # -----------------------------
    tf_config = TIMEFRAME_CONFIG[timeframe]
    period = tf_config["period"]
    interval = tf_config["interval"]
    intraday = tf_config["intraday"]

    data = fetch_data(ticker, period, interval)

    if data.empty:
        st.error(f"No price data found for {ticker} in {timeframe}. Try another timeframe or verify the symbol.")
        st.stop()

    # resample
    if tf_config["resample"]:
        data = resample_df(data, timeframe)

    if data.empty:
        st.error(f"No candles available for {ticker} after applying the {timeframe} timeframe.")
        st.stop()

    # safety
    if len(data) < 30:
        st.warning("Not enough data for indicators")
        st.stop()

    data = add_indicators(data, intraday)

    signal, score, cond = analyze(data, intraday)

    # -----------------------------
    # LAYOUT
    # -----------------------------
    col1, col2 = st.columns([2,1])

    with col1:
        st.plotly_chart(plot_chart(data, intraday), use_container_width=True)

    with col2:
        st.subheader(f"Signal: {signal}")
        st.write(f"Score: {score}")

        for k,v in cond.items():
            st.write(f"{k}: {'✔️' if v else '❌'}")

        st.markdown("### AI Insight")
        st.write(ai_explain(signal, cond))

    # -----------------------------
    # TREND CONFIRMATION
    # -----------------------------
    daily = fetch_data(ticker, "6mo", "1d")

    if not daily.empty and len(daily) > 30:
        daily = add_indicators(daily, False)
        d_signal,_,_ = analyze(daily, False)

        st.markdown("### Trend Confirmation")
        st.write(f"Daily Trend: {d_signal}")

        if signal == "BUY" and d_signal == "BUY":
            st.success("Strong BUY")
        elif signal == "BUY" and d_signal == "SELL":
            st.warning("Weak BUY")
        elif signal == "SELL" and d_signal == "SELL":
            st.error("Strong SELL")
        else:
            st.info("Mixed → HOLD")

    # -----------------------------
    # PAPER TRADE
    # -----------------------------
    st.markdown("### 📄 Paper Trading")

    if st.button("Execute Paper Trade"):
        price = data["Close"].iloc[-1]
        qty = int(10000 / price)

        if signal == "BUY":
            sl = price * 0.98
            target = price * 1.03
        else:
            sl = price * 1.02
            target = price * 0.97

        st.success(
            f"{signal} | Entry: {price:.2f} | SL: {sl:.2f} | Target: {target:.2f} | Qty: {qty}"
        )

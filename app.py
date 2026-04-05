from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots


st.set_page_config(
    page_title="Stock Analyzer Pro",
    page_icon="📈",
    layout="wide",
)


COMMON_MAP = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "microsoft": "MSFT",
    "pepsi": "PEP",
    "walmart": "WMT",
    "washington": "WASH",
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",
    "sbin": "SBIN.NS",
}

TIMEFRAME_CONFIG = {
    "1min": {"period": "7d", "interval": "1m", "resample": None, "intraday": True},
    "3min": {"period": "7d", "interval": "1m", "resample": "3min", "intraday": True},
    "5min": {"period": "30d", "interval": "5m", "resample": None, "intraday": True},
    "10min": {"period": "30d", "interval": "5m", "resample": "10min", "intraday": True},
    "15min": {"period": "30d", "interval": "15m", "resample": None, "intraday": True},
    "1hour": {"period": "730d", "interval": "60m", "resample": None, "intraday": True},
    "4hour": {"period": "730d", "interval": "60m", "resample": "4h", "intraday": True},
    "8hour": {"period": "730d", "interval": "60m", "resample": "8h", "intraday": True},
    "1day": {"period": "5y", "interval": "1d", "resample": None, "intraday": False},
    "2days": {"period": "5y", "interval": "1d", "resample": "2D", "intraday": False},
    "5days": {"period": "10y", "interval": "1d", "resample": "5D", "intraday": False},
    "7days": {"period": "10y", "interval": "1d", "resample": "7D", "intraday": False},
    "1month": {"period": "10y", "interval": "1d", "resample": "1M", "intraday": False},
    "2months": {"period": "10y", "interval": "1d", "resample": "2M", "intraday": False},
    "3months": {"period": "10y", "interval": "1d", "resample": "3M", "intraday": False},
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.18), transparent 28%),
                radial-gradient(circle at top left, rgba(30, 64, 175, 0.18), transparent 24%),
                linear-gradient(180deg, #07111f 0%, #0b1220 100%);
            color: #ecf3ff;
        }
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 18px;
            padding: 14px;
        }
        .hero-card, .info-card {
            background: rgba(15, 23, 42, 0.78);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 22px;
            padding: 20px 22px;
            box-shadow: 0 18px 40px rgba(2, 6, 23, 0.25);
        }
        .hero-card h1, .info-card h3 {
            margin: 0;
            color: #f8fafc;
        }
        .muted-text {
            color: #94a3b8;
            font-size: 0.95rem;
        }
        .signal-buy, .signal-sell, .signal-hold {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        .signal-buy {
            background: rgba(16, 185, 129, 0.18);
            color: #6ee7b7;
        }
        .signal-sell {
            background: rgba(239, 68, 68, 0.16);
            color: #fda4af;
        }
        .signal-hold {
            background: rgba(250, 204, 21, 0.15);
            color: #fde68a;
        }
        .score-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 14px;
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid rgba(148, 163, 184, 0.12);
            margin-bottom: 10px;
        }
        .pill {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            background: rgba(59, 130, 246, 0.18);
            color: #bfdbfe;
            font-size: 0.8rem;
            margin-right: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    cleaned = df.copy()
    cleaned = cleaned.loc[:, [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in cleaned.columns]]
    cleaned = cleaned.dropna(subset=[c for c in ["Open", "High", "Low", "Close"] if c in cleaned.columns])

    if "Volume" not in cleaned.columns:
        cleaned["Volume"] = 0

    return cleaned.sort_index()


@st.cache_data(ttl=300, show_spinner=False)
def search_candidates(query: str) -> List[Dict]:
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip()
    endpoints = [
        ("https://query2.finance.yahoo.com/v1/finance/search", {"q": q, "quotesCount": 8, "newsCount": 0}),
        ("https://query1.finance.yahoo.com/v1/finance/search", {"q": q, "quotesCount": 8, "newsCount": 0}),
    ]
    headers = {"User-Agent": "Mozilla/5.0"}

    for url, params in endpoints:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=6)
            response.raise_for_status()
            payload = response.json()
            results = []
            for item in payload.get("quotes", []):
                symbol = item.get("symbol")
                name = item.get("shortname") or item.get("longname") or item.get("symbol")
                exchange = item.get("exchangeDisp") or item.get("exchange")
                quote_type = item.get("quoteType")
                if not symbol or quote_type not in {None, "EQUITY", "ETF"}:
                    continue
                results.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "exchange": exchange or "Market",
                        "label": f"{name} ({symbol}) - {exchange or 'Market'}",
                    }
                )
            if results:
                seen = set()
                unique = []
                for item in results:
                    if item["symbol"] in seen:
                        continue
                    seen.add(item["symbol"])
                    unique.append(item)
                return unique
        except requests.RequestException:
            continue
        except ValueError:
            continue

    return []


def resolve_symbol(query: str) -> Tuple[Optional[str], List[Dict], Optional[str]]:
    if not query or not query.strip():
        return None, [], "Type at least 2 characters to search."

    normalized = query.strip()
    lowered = normalized.lower()

    if lowered in COMMON_MAP:
        return COMMON_MAP[lowered], [], None

    for key, value in COMMON_MAP.items():
        if key in lowered:
            return value, [], None

    candidates = search_candidates(normalized)
    if candidates:
        upper_query = normalized.upper()
        for item in candidates:
            if item["symbol"].upper() == upper_query:
                return item["symbol"], candidates, None
        return candidates[0]["symbol"], candidates, None

    possible = normalized.upper()
    probe_targets = [possible]
    if not possible.endswith(".NS"):
        probe_targets.append(f"{possible}.NS")

    for symbol in probe_targets:
        probe = fetch_market_data(symbol, "5d", "1d")
        if not probe.empty:
            return symbol, [], None

    return None, [], f"No listed stock matched '{normalized}'."


@st.cache_data(ttl=120, show_spinner=False)
def fetch_market_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        return sanitize_dataframe(data)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_company_info(ticker: str) -> Dict:
    try:
        info = yf.Ticker(ticker).info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def resample_price_data(df: pd.DataFrame, rule: Optional[str]) -> pd.DataFrame:
    if df.empty or not rule:
        return df

    resampled = (
        df.resample(rule)
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna()
    )
    return resampled


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = enriched["Close"]

    enriched["EMA9"] = close.ewm(span=9, adjust=False).mean()
    enriched["EMA21"] = close.ewm(span=21, adjust=False).mean()
    enriched["MA20"] = close.rolling(20).mean()
    enriched["MA50"] = close.rolling(50).mean()
    enriched["MA200"] = close.rolling(200).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, pd.NA)
    rs = gain / loss
    enriched["RSI"] = 100 - (100 / (1 + rs))

    cumulative_volume = enriched["Volume"].replace(0, pd.NA).cumsum()
    enriched["VWAP"] = ((enriched["Close"] * enriched["Volume"]).cumsum() / cumulative_volume).fillna(method="ffill")
    enriched["VolumeAvg20"] = enriched["Volume"].rolling(20).mean()
    enriched["VolumeRatio"] = enriched["Volume"] / enriched["VolumeAvg20"].replace(0, pd.NA)

    return enriched.dropna()


def build_scorecard(df: pd.DataFrame, horizon: str, fundamentals: Optional[Dict] = None) -> Dict:
    latest = df.iloc[-1]
    weights = []

    if horizon == "intraday":
        weights = [
            {
                "name": "Price above EMA9",
                "weight": 15,
                "passed": latest["Close"] > latest["EMA9"],
                "value": f"{latest['Close']:.2f} vs {latest['EMA9']:.2f}",
                "reason": "Shows short-term momentum is still strong.",
            },
            {
                "name": "EMA9 above EMA21",
                "weight": 25,
                "passed": latest["EMA9"] > latest["EMA21"],
                "value": f"{latest['EMA9']:.2f} vs {latest['EMA21']:.2f}",
                "reason": "Confirms fast trend is stronger than the recent base trend.",
            },
            {
                "name": "RSI in active zone",
                "weight": 20,
                "passed": 45 <= latest["RSI"] <= 68,
                "value": f"RSI {latest['RSI']:.1f}",
                "reason": "Healthy momentum without being too overheated.",
            },
            {
                "name": "Price above VWAP",
                "weight": 20,
                "passed": latest["Close"] > latest["VWAP"],
                "value": f"{latest['Close']:.2f} vs {latest['VWAP']:.2f}",
                "reason": "Buyers are controlling the session average price.",
            },
            {
                "name": "Volume participation",
                "weight": 20,
                "passed": latest["VolumeRatio"] >= 1.1,
                "value": f"{latest['VolumeRatio']:.2f}x average",
                "reason": "Volume is supporting the move instead of fading it.",
            },
        ]
    elif horizon == "swing":
        weights = [
            {
                "name": "Price above MA20",
                "weight": 15,
                "passed": latest["Close"] > latest["MA20"],
                "value": f"{latest['Close']:.2f} vs {latest['MA20']:.2f}",
                "reason": "Shows the stock is holding above the short swing trend.",
            },
            {
                "name": "Price above MA50",
                "weight": 20,
                "passed": latest["Close"] > latest["MA50"],
                "value": f"{latest['Close']:.2f} vs {latest['MA50']:.2f}",
                "reason": "Keeps the medium trend supportive for a swing setup.",
            },
            {
                "name": "EMA9 above EMA21",
                "weight": 20,
                "passed": latest["EMA9"] > latest["EMA21"],
                "value": f"{latest['EMA9']:.2f} vs {latest['EMA21']:.2f}",
                "reason": "Recent momentum still points upward.",
            },
            {
                "name": "RSI balanced",
                "weight": 15,
                "passed": 45 <= latest["RSI"] <= 70,
                "value": f"RSI {latest['RSI']:.1f}",
                "reason": "Momentum is supportive without screaming exhaustion.",
            },
            {
                "name": "Volume confirmation",
                "weight": 10,
                "passed": latest["VolumeRatio"] >= 1.0,
                "value": f"{latest['VolumeRatio']:.2f}x average",
                "reason": "Breakouts are cleaner when volume is at least average.",
            },
            {
                "name": "Above 20-session breakout zone",
                "weight": 20,
                "passed": latest["Close"] >= df["High"].rolling(20).max().iloc[-1] * 0.98,
                "value": f"{latest['Close']:.2f}",
                "reason": "Price is trading close to its recent breakout band.",
            },
        ]
    else:
        fundamentals = fundamentals or {}
        revenue_growth = fundamentals.get("revenueGrowth")
        profit_margins = fundamentals.get("profitMargins")
        trailing_pe = fundamentals.get("trailingPE")

        weights = [
            {
                "name": "Price above MA50",
                "weight": 20,
                "passed": latest["Close"] > latest["MA50"],
                "value": f"{latest['Close']:.2f} vs {latest['MA50']:.2f}",
                "reason": "The stock is holding above its medium-term trend.",
            },
            {
                "name": "MA50 above MA200",
                "weight": 25,
                "passed": latest["MA50"] > latest["MA200"],
                "value": f"{latest['MA50']:.2f} vs {latest['MA200']:.2f}",
                "reason": "This is a classic long-term trend confirmation.",
            },
            {
                "name": "RSI constructive",
                "weight": 10,
                "passed": 45 <= latest["RSI"] <= 70,
                "value": f"RSI {latest['RSI']:.1f}",
                "reason": "Momentum is positive but not deeply overbought.",
            },
            {
                "name": "Revenue growth positive",
                "weight": 15,
                "passed": revenue_growth is not None and revenue_growth > 0,
                "value": "N/A" if revenue_growth is None else f"{revenue_growth * 100:.1f}%",
                "reason": "Positive top-line growth supports longer-term compounding.",
            },
            {
                "name": "Profit margins positive",
                "weight": 15,
                "passed": profit_margins is not None and profit_margins > 0,
                "value": "N/A" if profit_margins is None else f"{profit_margins * 100:.1f}%",
                "reason": "A profitable business can sustain trend strength better.",
            },
            {
                "name": "Valuation not stretched",
                "weight": 15,
                "passed": trailing_pe is not None and 0 < trailing_pe < 45,
                "value": "N/A" if trailing_pe is None else f"PE {trailing_pe:.1f}",
                "reason": "Very high valuations can weaken long-term risk/reward.",
            },
        ]

    total_weight = sum(item["weight"] for item in weights)
    achieved = sum(item["weight"] for item in weights if item["passed"])
    score = round((achieved / total_weight) * 100) if total_weight else 0

    if score >= 70:
        signal = "BUY"
    elif score <= 40:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {"signal": signal, "score": score, "items": weights}


def recommendation_summary(signal: str, horizon: str) -> str:
    if signal == "BUY":
        if horizon == "intraday":
            return "Momentum supports an intraday long bias, but entries are best on pullbacks near VWAP or EMA9."
        if horizon == "swing":
            return "Trend and momentum are aligned for a swing setup if price holds above recent breakout support."
        return "Long-term trend and available business signals are supportive for accumulation on staggered entries."
    if signal == "SELL":
        if horizon == "intraday":
            return "Intraday structure is weak. Avoid fresh longs unless price reclaims VWAP and fast EMAs."
        if horizon == "swing":
            return "Swing structure is deteriorating, so risk control matters more than upside chasing."
        return "Long-term setup lacks strength right now; patience is better than forcing exposure."
    return "The setup is mixed. Waiting for price confirmation can improve risk/reward."


def build_fundamental_snapshot(info: Dict) -> List[Tuple[str, str]]:
    market_cap = info.get("marketCap")
    pe = info.get("trailingPE")
    revenue_growth = info.get("revenueGrowth")
    profit_margins = info.get("profitMargins")
    dividend_yield = info.get("dividendYield")

    def human_number(value):
        if value is None:
            return "N/A"
        abs_value = abs(value)
        if abs_value >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.2f}T"
        if abs_value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        if abs_value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        return f"{value:,.0f}"

    return [
        ("Market Cap", human_number(market_cap)),
        ("PE Ratio", "N/A" if pe is None else f"{pe:.2f}"),
        ("Revenue Growth", "N/A" if revenue_growth is None else f"{revenue_growth * 100:.1f}%"),
        ("Profit Margin", "N/A" if profit_margins is None else f"{profit_margins * 100:.1f}%"),
        ("Dividend Yield", "N/A" if dividend_yield is None else f"{dividend_yield * 100:.1f}%"),
    ]


def plot_chart(df: pd.DataFrame, timeframe_label: str) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.76, 0.24],
        vertical_spacing=0.05,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA9"], name="EMA9", line={"color": "#38bdf8", "width": 1.5}), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA21"], name="EMA21", line={"color": "#f59e0b", "width": 1.5}), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP", line={"color": "#a78bfa", "width": 1.2}), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color="#334155", opacity=0.8), row=2, col=1)

    fig.update_layout(
        height=720,
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        paper_bgcolor="rgba(2, 6, 23, 0)",
        plot_bgcolor="rgba(15, 23, 42, 0.68)",
        font={"color": "#e2e8f0"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        xaxis_rangeslider_visible=False,
        title=f"{timeframe_label} price action",
    )
    fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.08)")
    fig.update_xaxes(gridcolor="rgba(148, 163, 184, 0.08)")
    return fig


def render_scorecard(title: str, card: Dict, horizon: str) -> None:
    signal_class = f"signal-{card['signal'].lower()}"
    st.markdown(
        f"""
        <div class="info-card">
            <div class="{signal_class}">{title}: {card['signal']}</div>
            <h3 style="margin-top:12px;">Score {card['score']}/100</h3>
            <p class="muted-text">{recommendation_summary(card['signal'], horizon)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(card["score"] / 100)

    for item in card["items"]:
        status = "PASS" if item["passed"] else "MISS"
        st.markdown(
            f"""
            <div class="score-row">
                <div>
                    <strong>{item['name']}</strong><br/>
                    <span class="muted-text">{item['reason']}</span>
                </div>
                <div style="text-align:right;">
                    <div><strong>{status}</strong></div>
                    <div class="muted-text">{item['value']}</div>
                    <div class="muted-text">Weight {item['weight']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_search_feedback(query: str, suggestions: List[Dict]) -> None:
    st.error(f"No listed stock matched '{query}'.")
    if suggestions:
        st.caption("Closest matches from Yahoo Finance search:")
        for item in suggestions[:5]:
            st.markdown(f"- `{item['symbol']}`: {item['name']} ({item['exchange']})")
    else:
        st.info("Try a company name, NSE symbol with `.NS`, or a popular ticker like `AAPL`, `INFY.NS`, `RELIANCE.NS`.")


def prepare_analysis_dataset(ticker: str, timeframe_label: str) -> Tuple[pd.DataFrame, Optional[str]]:
    config = TIMEFRAME_CONFIG[timeframe_label]
    raw = fetch_market_data(ticker, config["period"], config["interval"])
    if raw.empty:
        return pd.DataFrame(), "Price feed returned no rows for this stock and timeframe."

    if config["resample"]:
        raw = resample_price_data(raw, config["resample"])

    enriched = add_indicators(raw)
    if enriched.empty or len(enriched) < 20:
        return pd.DataFrame(), "Not enough historical candles to compute indicators reliably."

    return enriched, None


inject_styles()

if "selected_symbol" not in st.session_state:
    st.session_state.selected_symbol = ""

if "selected_label" not in st.session_state:
    st.session_state.selected_label = "15min"


st.markdown(
    """
    <div class="hero-card">
        <span class="pill">Live analysis</span>
        <span class="pill">Technical + fundamentals</span>
        <span class="pill">Intraday + swing + investing</span>
        <h1>Stock Analyzer Pro</h1>
        <p class="muted-text" style="margin-top:10px;">
            Search any stock, inspect multi-timeframe trend strength, and see exactly how the recommendation score is built.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

toolbar_col1, toolbar_col2 = st.columns([4, 1])
with toolbar_col1:
    query = st.text_input(
        "Search stock",
        value=st.session_state.selected_symbol,
        placeholder="Try RELIANCE, TCS, INFY.NS, AAPL, Tesla...",
    )
with toolbar_col2:
    st.write("")
    st.write("")
    if st.button("Refresh data", use_container_width=True):
        fetch_market_data.clear()
        fetch_company_info.clear()
        search_candidates.clear()
        st.rerun()

selected_ticker = None
search_options = []

if query and len(query.strip()) >= 2:
    default_ticker, search_options, search_error = resolve_symbol(query)
    if search_options:
        labels = [item["label"] for item in search_options]
        default_index = 0
        for idx, item in enumerate(search_options):
            if item["symbol"] == default_ticker:
                default_index = idx
                break
        selected_label = st.selectbox("Suggestions", labels, index=default_index)
        selected_ticker = next(item["symbol"] for item in search_options if item["label"] == selected_label)
    else:
        selected_ticker = default_ticker

    if not selected_ticker:
        render_search_feedback(query.strip(), search_options)
        st.stop()
else:
    search_error = "Type at least 2 characters to begin."

if not selected_ticker:
    st.info(search_error)
    st.stop()

st.session_state.selected_symbol = selected_ticker

timeframe_col1, timeframe_col2, timeframe_col3 = st.columns([2.4, 1.2, 1.4])
with timeframe_col1:
    timeframe = st.selectbox("Chart timeframe", list(TIMEFRAME_CONFIG.keys()), index=list(TIMEFRAME_CONFIG.keys()).index(st.session_state.selected_label))
with timeframe_col2:
    auto_refresh = st.toggle("Auto context refresh", value=False, help="Re-runs lightweight search/data caches when you interact.")
with timeframe_col3:
    st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y %I:%M:%S %p')}")

st.session_state.selected_label = timeframe

if auto_refresh:
    fetch_market_data.clear()

analysis_df, analysis_error = prepare_analysis_dataset(selected_ticker, timeframe)
if analysis_error:
    st.error(analysis_error)
    st.stop()

daily_df = fetch_market_data(selected_ticker, "3y", "1d")
daily_enriched = add_indicators(daily_df) if not daily_df.empty else pd.DataFrame()
company_info = fetch_company_info(selected_ticker)

intraday_card = build_scorecard(analysis_df, "intraday" if TIMEFRAME_CONFIG[timeframe]["intraday"] else "swing")
swing_card = build_scorecard(daily_enriched, "swing") if len(daily_enriched) >= 60 else {"signal": "HOLD", "score": 50, "items": []}
long_term_card = build_scorecard(daily_enriched, "long_term", company_info) if len(daily_enriched) >= 220 else {"signal": "HOLD", "score": 50, "items": []}

latest_close = analysis_df["Close"].iloc[-1]
previous_close = analysis_df["Close"].iloc[-2]
change_pct = ((latest_close - previous_close) / previous_close) * 100 if previous_close else 0

overview1, overview2, overview3, overview4 = st.columns(4)
overview1.metric("Selected stock", selected_ticker)
overview2.metric("Last close", f"{latest_close:.2f}", f"{change_pct:.2f}%")
overview3.metric("Intraday / chart call", intraday_card["signal"], f"{intraday_card['score']}/100")
overview4.metric("Long-term view", long_term_card["signal"], f"{long_term_card['score']}/100")

tabs = st.tabs(["Overview", "Technical Score", "Fundamentals", "Trading Views"])

with tabs[0]:
    left, right = st.columns([2.3, 1])
    with left:
        st.plotly_chart(plot_chart(analysis_df, timeframe), use_container_width=True)
    with right:
        render_scorecard("Chart recommendation", intraday_card, "intraday" if TIMEFRAME_CONFIG[timeframe]["intraday"] else "swing")
        st.markdown("### Why this stock")
        st.write(
            f"Price is currently at `{latest_close:.2f}` for `{selected_ticker}`. "
            f"The current chart recommendation is `{intraday_card['signal']}` because the weighted technical score came to `{intraday_card['score']}/100`."
        )
        st.markdown("### Action style")
        st.write(f"Intraday: {recommendation_summary(intraday_card['signal'], 'intraday')}")
        st.write(f"Swing: {recommendation_summary(swing_card['signal'], 'swing')}")
        st.write(f"Long term: {recommendation_summary(long_term_card['signal'], 'long_term')}")

with tabs[1]:
    tech_left, tech_right = st.columns(2)
    with tech_left:
        render_scorecard("Intraday / active trade", intraday_card, "intraday" if TIMEFRAME_CONFIG[timeframe]["intraday"] else "swing")
    with tech_right:
        if swing_card["items"]:
            render_scorecard("Swing trade", swing_card, "swing")
        else:
            st.warning("Swing score needs at least 60 daily candles.")

    st.markdown("### Indicator guide")
    st.write("`EMA9 / EMA21`: fast trend direction. `VWAP`: fair intraday price benchmark. `RSI`: momentum heat gauge. `MA20 / MA50 / MA200`: trend quality across swing and investing timeframes.")

with tabs[2]:
    fund_left, fund_right = st.columns([1, 1.2])
    with fund_left:
        st.markdown("### Fundamental snapshot")
        for label, value in build_fundamental_snapshot(company_info):
            st.write(f"**{label}:** {value}")
        if not company_info:
            st.info("Fundamental fields were not available from Yahoo Finance for this ticker.")
    with fund_right:
        if long_term_card["items"]:
            render_scorecard("Long-term investing", long_term_card, "long_term")
        else:
            st.warning("Long-term score needs about 200 daily candles plus available fundamentals.")

with tabs[3]:
    intraday_box, swing_box, long_box = st.columns(3)
    with intraday_box:
        st.markdown("### Intraday")
        st.write(f"Recommendation: **{intraday_card['signal']}**")
        st.write(recommendation_summary(intraday_card["signal"], "intraday"))
    with swing_box:
        st.markdown("### Swing")
        st.write(f"Recommendation: **{swing_card['signal']}**")
        st.write(recommendation_summary(swing_card["signal"], "swing"))
    with long_box:
        st.markdown("### Long term")
        st.write(f"Recommendation: **{long_term_card['signal']}**")
        st.write(recommendation_summary(long_term_card["signal"], "long_term"))

    st.markdown("### What to do when stock is not available")
    st.write(
        "The app now handles missing symbols by trying a common-name map, Yahoo search suggestions, and an NSE fallback. "
        "If nothing matches, it shows a clear error plus likely alternatives instead of a dead-end 'No data found'."
    )

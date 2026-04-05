import json
from datetime import datetime

FILE = "trades.json"


def load_trades():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_trades(trades):
    with open(FILE, "w") as f:
        json.dump(trades, f, indent=2)


def calculate_position_size(entry, stop_loss, risk=100):
    risk_per_share = abs(entry - stop_loss)
    if risk_per_share == 0:
        return 0
    return int(risk / risk_per_share)


def create_trade(ticker, signal, entry):
    if signal == "BUY":
        sl = entry * 0.98
        target = entry * 1.04
    else:
        sl = entry * 1.02
        target = entry * 0.96

    qty = calculate_position_size(entry, sl)

    trade = {
        "ticker": ticker,
        "signal": signal,
        "entry": entry,
        "stop_loss": round(sl, 2),
        "target": round(target, 2),
        "quantity": qty,
        "status": "OPEN",
        "pnl": 0,
        "time": datetime.now().isoformat()
    }

    trades = load_trades()
    trades.append(trade)
    save_trades(trades)

    return trade


def update_trade_status(trade, current_price):
    if trade["status"] == "CLOSED":
        return trade

    if trade["signal"] == "BUY":
        if current_price <= trade["stop_loss"]:
            trade["status"] = "CLOSED"
            trade["pnl"] = (trade["stop_loss"] - trade["entry"]) * trade["quantity"]

        elif current_price >= trade["target"]:
            trade["status"] = "CLOSED"
            trade["pnl"] = (trade["target"] - trade["entry"]) * trade["quantity"]

    else:
        if current_price >= trade["stop_loss"]:
            trade["status"] = "CLOSED"
            trade["pnl"] = (trade["entry"] - trade["stop_loss"]) * trade["quantity"]

        elif current_price <= trade["target"]:
            trade["status"] = "CLOSED"
            trade["pnl"] = (trade["entry"] - trade["target"]) * trade["quantity"]

    return trade


def calculate_pnl(trade, current):
    if trade["signal"] == "BUY":
        return (current - trade["entry"]) * trade["quantity"]
    else:
        return (trade["entry"] - current) * trade["quantity"]
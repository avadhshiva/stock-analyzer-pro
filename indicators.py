import pandas as pd

def calculate_indicators(data):
    close = data['Close']

    data['MA20'] = close.rolling(20).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()

    rs = gain / loss.replace(0, pd.NA)
    data['RSI'] = 100 - (100 / (1 + rs))

    data['EMA9'] = close.ewm(span=9).mean()
    data['EMA21'] = close.ewm(span=21).mean()

    data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()

    return data.dropna()
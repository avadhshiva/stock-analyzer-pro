import requests

def search_stocks(query):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": query, "quotesCount": 5, "newsCount": 0}

    try:
        response = requests.get(url, params=params)
        data = response.json()

        results = []
        for item in data.get("quotes", []):
            symbol = item.get("symbol")
            name = item.get("shortname")

            if symbol and name:
                results.append(f"{name} ({symbol})")

        return results

    except Exception as e:
        print("Search error:", e)
        return []
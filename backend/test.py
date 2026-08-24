import requests

def suggestions(query):
    url = "https://duckduckgo.com/ac/"
    params = {
        "q": query,
        "kl": "us-en",
    }

    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()

    return [item["phrase"] for item in response.json()]

print(suggestions("pyth"))
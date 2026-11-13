"""What two common Python clients do with list and dict query values.

Author: Sandeep Belgavi. Prepares requests without sending them.
"""
from urllib.parse import urlencode
import requests

URL = "https://api.books.example.test/orders"
cases = {
    "list": {"status": ["open", "returned"]},
    "dict": {"filter": {"author": "Geetha", "year": 2026}},
}
if __name__ == "__main__":
    print("requests", requests.__version__)
    for name, params in cases.items():
        print(name, "requests:", requests.Request("GET", URL, params=params).prepare().url.split("?", 1)[1])
        print(name, "urlencode(doseq=False):", urlencode(params))
        print(name, "urlencode(doseq=True):", urlencode(params, doseq=True))

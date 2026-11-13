# OpenAPI style and explode serialization

**Author: Sandeep Belgavi**

A runnable companion to *OpenAPI style and explode: How Array and Object Query Parameters Reach the Wire* (aicassindra.com). An original serializer for OpenAPI 3.1 parameter styles (matrix, label, simple, form, spaceDelimited, pipeDelimited, deepObject) with tests for every cell of the specification's Style Examples table, plus a script showing what Python requests and urllib.parse.urlencode do with list and dict values.

## Prerequisites

- Python 3.11 or newer. The serializer and its tests use only the standard library; client_behaviour.py needs requests.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

The specification's own example values: "blue", ["blue", "black", "brown"] and {"R": 100, "G": 200, "B": 150}.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
python -m pip install -r requirements.txt
python client_behaviour.py
```

## Expected output

37 specified cells match and every n/a cell raises ValueError; 4 tests pass. With requests 2.34.2 a list becomes status=open&status=returned and a dict value becomes filter=author&filter=year (keys only); urlencode without doseq sends the Python repr.

## Limitations

Primitives are converted with str(); allowReserved, content-typed parameters and cookie encoding are not covered.

Views are my own and do not represent any employer, past or present.

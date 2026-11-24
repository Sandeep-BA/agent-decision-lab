# Resume HTTP Downloads Without Joining Bytes From Different Versions

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Bind a partial file to a strong validator and distinguish appendable 206 responses from replacement 200 responses.

Article destination (publication pending): https://aicassindra.com/blogs/networking/http_if_range_download_resume.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Single parsed suffix with ASCII fixtures; no network, complete header parser, multipart range, integrity check or crash-safe filesystem writes.

Views are my own and do not represent any employer, past or present.

## Primary references

- [RFC 9110, June 2022: If-Range and partial content](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.5)

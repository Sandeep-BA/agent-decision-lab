# Spring Boot 4.2 Moves Forwarded Header Settings Under server.request.header.forwarded

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/java/spring_boot_4_2_forwarded_header_properties.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: A static checker for flat .properties input that encodes rules from Spring Boot v4.2.0 sources. It does not start Spring, read YAML or environment variables, or implement every relaxed-binding form. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.

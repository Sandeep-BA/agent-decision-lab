# CSV exports that cannot start a formula

**Author: Sandeep Belgavi**

A runnable companion to *CSV Exports That Run Formulas: Neutralizing Spreadsheet Injection* (aicassindra.com). A CSV writer that quotes every field and prefixes cells starting with a formula trigger, following the OWASP CSV Injection guidance, with an option for the tab prefix OWASP describes for Excel.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Five synthetic help-desk rows in `ROWS`, including a `=HYPERLINK(...)` customer name and a full-width equals sign. Run `python safe_csv.py` to print both exports.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Seven tests pass. The unsafe export contains five cells that start with a trigger; the safe export contains none except the numeric refund -3.0 when that column is declared numeric.

## Limitations

No spreadsheet application was run. Behaviour on open, on save and re-open, and with DDE differs between applications and versions; OWASP notes that Excel can drop the quote prefix on save.

Views are my own and do not represent any employer, past or present.

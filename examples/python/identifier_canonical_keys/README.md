# identifier_canonical_keys

**Author: Sandeep Belgavi**

Companion to the guide *Two Usernames That Look the Same: Unicode Normalization and Unique Keys*
on aicassindra.com. It replays ten synthetic sign-ups for Belgavi's Book Store against four ways of
enforcing a unique username and counts which ones store a duplicate or an invisible character.

- `canonical.py`: `username_key()` (width mapping, `lower()`, NFC, then a simplified check that rejects
  control, format, private-use, unassigned and space characters, in the order of the RFC 8265
  UsernameCaseMapped profile) and `skeleton()` (UTS #39: NFD, confusables mapping, NFD).
- `signups.json`: the existing accounts and the ten attempts, with escapes for every non-ASCII character.
- `confusables_subset.txt`: twelve lines copied unchanged from Unicode `confusables.txt` version 18.0.0
  (2026-08-06), with its copyright header. Use the full file in a real system.
- `demo.py`: the replay. `expected_output.txt` is its output on the tested setup.

## Prerequisites

Python 3.11 or newer. Standard library only (`unicodedata`, `sqlite3`). Tested with Python 3.13.5,
whose `unicodedata` is Unicode 15.1.0. No environment variables are needed (`.env.example` is empty
on purpose).

## Run

From this directory:

```
python demo.py
python -m unittest -v
```

Expected summary (see `expected_output.txt` for every row):

```
raw UNIQUE     wrong outcomes: 7 of 10
SQLite NOCASE  wrong outcomes: 5 of 10
lower()        wrong outcomes: 4 of 10
username_key   wrong outcomes: 0 of 10
look-alike flags raised: 1
```

A wrong outcome is a stored duplicate, a stored invisible or space character, or a genuinely different
name refused. The Cyrillic look-alike is stored by every strategy; only the skeleton flags it for review.

## Limitations

- `username_key()` is not a complete PRECIS implementation. It does not derive the IdentifierClass from
  Unicode properties and does not apply the Bidi Rule. Use a maintained PRECIS library for production.
- The Unicode version of your runtime decides how new characters normalize and lowercase. Record it with
  the stored key and re-check keys when you upgrade.
- The ten sign-ups are a teaching fixture, not a survey of real attacks or an exhaustive test set.
- `skeleton()` with the twelve-line subset only knows those twelve mappings.

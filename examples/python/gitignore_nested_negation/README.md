# Subtree pruning and nested .gitignore negations

**Author: Sandeep Belgavi**

A runnable companion to *Pruning Ignored Directories Can Skip a Nested .gitignore That Re-Includes Files* (aicassindra.com). Three walkers over one synthetic tree: a model of git's rules, a walker that prunes every `dir/**` directory, and a guarded walker that prunes only when no negation could apply. Real `git status --ignored` is the oracle.

## Prerequisites

- Python 3.11 or newer and git on PATH for the oracle test (run here with git 2.46.0 on Windows). Standard library only.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`TREE` in `walk.py`: root `.gitignore` with `logs/**`, `build/**`, `*.tmp`; `logs/.gitignore` with `!keep.txt`; files under logs/, logs/sub/, build/ and src/.

## Commands

From this directory:

```
python walk.py
python -m unittest -v
```

## Expected output

git and the guarded walker keep `.gitignore`, `logs/keep.txt` and `src/app.py`; the naive walker loses `logs/keep.txt` and never reads `logs/.gitignore`. `logs/sub/keep.txt` stays ignored everywhere. The guarded walker still prunes build/. 6 tests pass (the oracle test is skipped without git).

## Limitations

Supports a small pattern subset, not full gitignore syntax (no character classes beyond fnmatch, no escaped `!`, no core.excludesFile). The guard treats any negation in loaded rules as blocking, which is safe but prunes less than it could.

Views are my own and do not represent any employer, past or present.

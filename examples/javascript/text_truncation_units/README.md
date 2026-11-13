# Truncating text by code units, code points, graphemes and bytes

**Author: Sandeep Belgavi**

A runnable companion to *Truncating Text Safely: UTF-16 Code Units, Code Points, Grapheme Clusters and UTF-8 Bytes* (aicassindra.com). Four truncation functions and a naive byte cut, each reported for lone surrogates, U+FFFD and broken grapheme clusters, using Intl.Segmenter and TextEncoder. The same functions back the interactive lab.

## Prerequisites

- Node.js 20 or newer (tested with 22.17.0). No dependencies.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

Synthetic strings: a ZWJ family emoji, a flag, a decomposed accent and repeated emoji, with the names Geetha and Jose.

## Commands

From this directory:

```
node truncate.mjs
node --test
```

## Expected output

The family emoji is 8 UTF-16 units, 5 code points, 1 grapheme and 18 UTF-8 bytes. Cutting "Order for <family> Geetha" at 11 UTF-16 units leaves a lone surrogate; code points at 13 split the ZWJ sequence; graphemes never split; a naive byte cut decodes to U+FFFD. 8 tests pass.

## Limitations

Grapheme rules come from the ICU data in your Node.js build. Terminal and font width are a separate problem.

Views are my own and do not represent any employer, past or present.

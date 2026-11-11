# Prompt templates and String.replace dollar patterns

**Author: Sandeep Belgavi**

A runnable companion to *Prompt Templates and String.replace: The Dollar Patterns Gemini CLI 0.68 Fixed* (aicassindra.com). Compares chained `String.prototype.replace` with string values, chained replacement with functions, and a single-pass renderer on case text that contains `$'`, `$$`, `$&`, `` $` `` and another placeholder.

## Prerequisites

- Node.js 22 or newer. No packages to install.
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`TEMPLATE` in `template.mjs` and the five case texts in `template.test.mjs`.

## Commands

From this directory:

```
node --test
node template.mjs
```

## Expected output

Thirteen tests pass. Chained string replacement corrupts all five inputs; the single-pass renderer leaves each literal; function replacement fixes the dollar patterns but still substitutes a placeholder that appeared inside inserted text.

## Limitations

Covers `{{name}}` placeholders only. It is an illustration of the language rule, not a copy of Gemini CLI code.

Views are my own and do not represent any employer, past or present.

# Redirect target validation with the WHATWG URL parser

**Author: Sandeep Belgavi**

A runnable companion to *Validating Redirect Targets With the Same URL Parser the Browser Uses* (aicassindra.com). Parses the requested target against a fixed base with the built-in `URL` class, checks scheme, userinfo, port and exact host, and returns the serialized URL to redirect to.

## Prerequisites

- Node.js 22 or newer. No packages to install (`package.json` is not needed).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

The `BAD` table in `redirect.test.mjs`: protocol-relative, backslash, embedded tab, userinfo, look-alike host, `javascript:`, plain `http:` and explicit-port targets.

## Commands

```
node --test
```

## Expected output

Twelve tests pass on Node.js 22. The two shortcut checks accept targets that the parser places on another host.

## Limitations

Covers only the redirect decision. It does not cover forwards inside a server, OAuth redirect_uri registration, or open redirects created by downstream pages.

Views are my own and do not represent any employer, past or present.

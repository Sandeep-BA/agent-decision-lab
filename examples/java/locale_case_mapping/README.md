# Default-locale case mapping and formatting in Java

**Author: Sandeep Belgavi**

A runnable companion to *Java toUpperCase Without a Locale: The Turkish I and Other Default-Locale Bugs* (aicassindra.com). Sets the JVM default locale to tr-TR and then de-DE inside a try/finally and records what `toUpperCase()`, `toLowerCase()`, `Enum.valueOf`, `equalsIgnoreCase` and `String.format` return with and without `Locale.ROOT`.

## Prerequisites

- A JDK 17 or newer. Tested with javac and java 23.0.2. No build tool and no dependencies.
- `.env.example` documents that nothing is read from the environment.

## Sample input

Synthetic strings in `LocaleCase.probe()`: `title`, `X-REQUEST-ID`, `pending_review`, `12.5`, `stra\u00dfe`.

## Commands

From this directory:

```
javac --release 17 -d build LocaleCase.java LocaleCaseTest.java
java -cp build LocaleCaseTest
java -cp build LocaleCase
```

## Expected output

`LocaleCaseTest` prints `13 checks passed`. Under tr-TR, `"title".toUpperCase()` is `T\u0130TLE` (dotted capital I), `"X-REQUEST-ID".toLowerCase()` is `x-request-\u0131d` (dotless small i) and `Status.valueOf` throws; with `Locale.ROOT` all three work. Under de-DE `String.format("%.2f", 12.5)` is `12,50`. Non-ASCII output is printed as escapes.

## Limitations

Shows JDK behaviour only. It does not scan your code; use a static analysis rule for calls without a Locale.

Views are my own and do not represent any employer, past or present.

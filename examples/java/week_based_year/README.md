# Week-based year versus calendar year in Java

**Author: Sandeep Belgavi**

A runnable companion to *YYYY Is Not the Year: Week-Based-Year Patterns in Java Date Formatting* (aicassindra.com). Formats dates around New Year 2027 with yyyy, YYYY and uuuu under Locale.US and Locale.UK with java.time and SimpleDateFormat, and lists every day where yyyy and YYYY disagree for seven year boundaries.

## Prerequisites

- A JDK 17 or newer. Tested with javac and java 23.0.2 using --release 17. No build tool and no dependencies.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Fixed dates in `WeekYear.probe()`; windows from 20 December to 10 January in `main`.

## Commands

From this directory:

```
javac --release 17 -d build WeekYear.java WeekYearTest.java
java -cp build WeekYearTest
java -cp build WeekYear
```

## Expected output

`WeekYearTest` prints `13 checks passed`. With Locale.US, 27 to 31 December 2026 format as 2027 under YYYY; with Locale.UK, 1 to 3 January 2027 format as 2026.

## Limitations

Results depend on the JDK locale data (CLDR by default). Other JDK vendors or locale providers could differ; rerun on your runtime.

Views are my own and do not represent any employer, past or present.

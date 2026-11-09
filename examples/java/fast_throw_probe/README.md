# HotSpot fast-throw probe

**Author: Sandeep Belgavi**

A runnable companion to *Why HotSpot Exceptions Can Lose Their Stack Traces* (aicassindra.com). Repeatedly dereferences a null string and counts exceptions whose stack trace is empty.

## Prerequisites

- A JDK with `javac`; the recorded run below used HotSpot 23.0.2+7-58. No third-party jars and no network.
- `.env.example` documents that nothing is read from the environment.

## Sample input

A single synthetic null reference; the argument sets the number of rounds.

## Commands

```
javac TraceProbe.java TraceProbeCheck.java
java TraceProbeCheck
java TraceProbe 1000000
java -XX:-OmitStackTraceInFastThrow TraceProbe 1000000
```

## Expected output

`java TraceProbeCheck` prints `checks passed:` followed by the counters. One recorded run on HotSpot 23.0.2+7-58 printed `rounds=1000000 empty=949243 first=5701` by default and `rounds=1000000 empty=0 first=-1` with the flag off. Your counts will differ; the first index varies by run and JVM.

## Limitations

Runtime-dependent. The portable check never requires an empty trace, and a run with no empty traces is a valid result. This is a diagnostic fixture, not a benchmark.

Views are my own and do not represent any employer, past or present.

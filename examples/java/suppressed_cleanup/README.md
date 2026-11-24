# Keep the Original Java Failure When Resource Cleanup Also Fails

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Observe primary and suppressed failures across body, initialization and reverse-order cleanup.

Article destination (publication pending): https://aicassindra.com/blogs/java/java_suppressed_exceptions_resource_cleanup.html

## Prerequisites

JDK 23.0.2 (the installed validation toolchain). No third-party dependencies.

## Run from this directory

```text
javac -d classes SuppressedExample.java TestCleanup.java
java -ea -cp classes SuppressedExample
java -ea -cp classes TestCleanup
```

The synthetic Java scenarios are hardcoded in the two source files; `sample-input.json` documents the primary scenario. Expected output: `expected-output.txt`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Synthetic AutoCloseable objects only. No real resource acquisition, durability or cleanup success is established.

Views are my own and do not represent any employer, past or present.

## Primary references

- [Java SE 25 language specification, section 14.20.3](https://docs.oracle.com/javase/specs/jls/se25/html/jls-14.html#jls-14.20.3)
- [Oracle Java tutorial: try-with-resources and suppressed exceptions](https://docs.oracle.com/javase/tutorial/essential/exceptions/tryResourceClose.html)

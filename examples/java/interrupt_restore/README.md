# Restore the interrupt status in Java workers

**Author: Sandeep Belgavi**

A runnable companion to *Restore the Interrupt When Java Code Catches InterruptedException* (aicassindra.com). Four single-thread executor tasks receive shutdownNow(): a polling loop that catches InterruptedException and continues, a queue poll loop that does the same, a loop that restores the flag and exits, and a loop that calls a helper which restores the flag so the caller's isInterrupted() check stops it. awaitTermination(500 ms) reports which executors stopped.

## Prerequisites

- JDK 17 or newer (run here with JDK 23.0.2). No build tool or dependencies.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Synthetic workers in `InterruptRestore.java`; no external input.

## Commands

From this directory:

```
javac --release 17 -d build InterruptRestore.java InterruptRestoreTest.java
java -cp build InterruptRestoreTest
java -cp build InterruptRestore
```

## Expected output

Swallowing loop and swallowing queue loop: not stopped within 500 ms, each caught exactly one interrupt. Propagating loop and restoring-helper loop: stopped. Thread.interrupted() called twice returns true, then false. 7 checks pass (JDK 23.0.2, compiled for release 17).

## Limitations

Timing-based checks on one machine; a heavily loaded machine could need a longer wait. Blocking I/O on classic streams does not respond to interrupts the same way; see the Thread.interrupt documentation.

Views are my own and do not represent any employer, past or present.

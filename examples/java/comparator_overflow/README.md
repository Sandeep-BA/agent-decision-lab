# Comparator overflow and the Comparator contract

**Author: Sandeep Belgavi**

A runnable companion to *Stop Java Comparator Overflow From Corrupting Your Sorted Collections* (aicassindra.com). Synthetic orders compared three ways: a `(int)` cast of a long millisecond difference, an int subtraction, and `Comparator.comparingLong(...).thenComparing(Order::id)`. Counts symmetry and transitivity violations over all pairs and triples, sorts 2,000 random orders over 120 days with 50 seeds, and shows a time-only `TreeSet` merging two orders.

## Prerequisites

- A JDK 17 or newer (run here with javac and java 23.0.2). No build tool and no dependencies.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Five orders in `fixture()`; random orders from `java.util.Random` seeds 1 to 50.

## Commands

From this directory:

```
javac --release 17 -d build ComparatorContract.java ComparatorContractTest.java
java -cp build ComparatorContractTest
java -cp build ComparatorContract
```

## Expected output

Orders 30 days apart compare the wrong way after truncation (1702967296). Transitivity violations: 12 truncated, 15 subtracted, 0 total-order. Time-only TreeSet holds 4 of 5 orders. Over seeds 1 to 50 the truncated comparator threw `IllegalArgumentException: Comparison method violates its general contract!` 14 times and returned a misordered array 36 times (JDK 23.0.2). `12 checks passed`.

## Limitations

The throw/silent split depends on the JDK sort implementation and the data; treat it as one measurement, not a rate.

Views are my own and do not represent any employer, past or present.

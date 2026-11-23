# Java records with array components

**Author: Sandeep Belgavi**

A runnable companion to *Java Records With Array Components Compare by Identity, Not Contents* (aicassindra.com). Shows that a record's generated equals, hashCode and toString treat an array component by reference, that the accessor exposes the array for writing, and two fixes: defensive copies with explicit methods, or a `List.copyOf` component.

## Prerequisites

- JDK 16 or newer (run here with Java 23.0.2). No build tool or dependencies; `requirements.txt` is not used for Java.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Return batch CASE-6101 with two synthetic ISBNs in `RecordArrays.java`.

## Commands

From this directory:

```
javac -d out RecordArrays.java RecordArraysTest.java
java -cp out RecordArrays
java -cp out RecordArraysTest
```

## Expected output

Generated equals on equal contents: false; HashSet.contains: false; toString prints `[Ljava.lang.String;@...`; writing through the accessor changes the record. The safe record and the List record compare by contents and resist the write. `11 checks passed`.

## Limitations

Plain-Java checks instead of JUnit to keep the example dependency-free. Element objects inside the array are not deep-copied; strings are immutable here.

Views are my own and do not represent any employer, past or present.

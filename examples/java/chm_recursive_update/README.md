# ConcurrentHashMap.computeIfAbsent Must Not Modify the Same Map From Its Function

Author: **Sandeep Belgavi**.

Original teaching probes for https://aicassindra.com/blogs/java/java_concurrenthashmap_recursive_update.html.

`RecursiveUpdate.java` memoises a recursive function with `computeIfAbsent` on a `ConcurrentHashMap` and on a `HashMap`, then shows two safe replacements (a loop, and get-then-`putIfAbsent`), a nested call on a different bin, a nested call on the same key, and two threads that nest into each other's keys (bounded by a 3-second timeout). `Frames.java` prints which method threw in each failing case (`computeIfAbsent` on a bin collision, `transfer` during a resize). `FibSweep.java` shows that whether the memoised version fails depends on the table size: the same code passes for small inputs and throws once the nested insertions collide with the reserved bin or trigger a resize.

Prerequisites: JDK 17 or newer (recorded with JDK 23.0.2). No dependencies, no network, no environment variables (`.env.example` documents that nothing is read).

```text
sh run.sh            # or: java RecursiveUpdate.java && java FibSweep.java && java Frames.java
```

Expected output: `expected.txt` (JDK 23.0.2 on Windows 11). The exact first failing input in the sweep can differ across JDK versions because it depends on table sizing and resize thresholds; the exception type and the deadlock do not.

Limitations: single-machine probes; the two-thread case is reported as "no progress after 3 s", which is how a deadlock appears to a caller, and the executor is abandoned with `System.exit`. Views are my own and do not represent any employer, past or present.

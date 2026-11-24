# Atomic Java file replacement

Author: **Sandeep Belgavi**.

Companion for https://aicassindra.com/blogs/java/java_atomic_file_replace_move.html (publication pending).

Prerequisites: JDK 23.0.2 (tested target); source uses Java 17-compatible APIs. No dependencies or environment variables.

From this directory, choose a directory name that does not exist:

```text
javac AtomicReplace.java
java AtomicReplace ./disposable-run-1
```

The run creates synthetic `generation:N` documents only inside that new directory. It tests input rejection, injected unsupported atomic movement, preservation of the old file, temporary-file cleanup and complete reader observations while attempting up to 100 replacements. `PASS` describes those invariant checks. The separate concurrent-replacement result states the actual completed count and any provider refusal; it must not be interpreted as 100 successful replacements. No retry or weaker fallback masks a refusal.

No cleanup of the supplied directory is automatic. Inspect it after the run. The example does not test power-loss durability, competing writers, arbitrary untrusted paths or multi-file transactions. Views are my own and do not represent any employer, past or present.

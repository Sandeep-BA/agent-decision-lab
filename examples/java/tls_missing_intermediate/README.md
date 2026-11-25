# A Server Missing Its Intermediate Certificate Works in Browsers and Fails in Java

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/security/tls_missing_intermediate_java_client.html (article publication pending).

Prerequisites: JDK 17 or newer with `keytool` and `java` on PATH, and a POSIX shell. No build tool or network access is needed.

From this directory:

```text
sh run.sh
```

`expected.txt` records the six result lines from a run on JDK 23.0.2. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: Synthetic EC P-256 certificates and a local HTTP stand-in for the AIA URL. Measured on JDK 23.0.2 only. Revocation, OCSP, cross-signing and name constraints are not tested; browser behaviour is not measured. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.

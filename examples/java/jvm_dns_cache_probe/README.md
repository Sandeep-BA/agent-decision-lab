# How Long the JVM Caches DNS Answers: networkaddress.cache.ttl, Negative Caching and a Resolver That Counts

Author: **Sandeep Belgavi**.

Original teaching probe for https://aicassindra.com/blogs/java/java_inetaddress_dns_cache_ttl.html.

`src/CountingResolverProvider.java` is an `InetAddressResolverProvider` (JEP 418, JDK 18+) registered through `META-INF/services`. It answers names under `.bookstore.test` with a synthetic address, counts every call and can be switched to failing. `src/DnsCacheProbe.java` sets the `networkaddress.cache.*` security properties before the first lookup, looks a name up once per second and prints when the resolver was actually consulted.

Prerequisites: JDK 18 or newer (recorded with JDK 23.0.2 on Windows 11). No dependencies, no network (the provider never queries DNS for `.bookstore.test`), and `.env.example` documents that nothing is read from the environment.

```text
sh run.sh
```

`run.sh` takes about two and a half minutes because the scenarios sleep in real time. Expected output: `expected-jdk23-windows.txt`. Recorded counts: default settings consulted the resolver at 0, 30.3 and 60.5 s over 65 lookups; `networkaddress.cache.ttl=5` every 5 s; `0` on every lookup; failed lookups were cached for 10 s; with `ttl=3` and the resolver failing from 5 s, lookups failed from 6 s without a stale window and kept succeeding until 15 s with `networkaddress.cache.stale.ttl=10`.

Limitations: timings are rounded to the one-second lookup interval and include scheduling jitter. The security properties are set programmatically before the first lookup; setting them later has no effect in this probe. Views are my own and do not represent any employer, past or present.

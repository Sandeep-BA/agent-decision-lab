# gRPC Java 1.86 Makes the Per-Address Pick-First Balancer the Default

Author: **Sandeep Belgavi**.

Original teaching model for https://aicassindra.com/blogs/networking/grpc_java_1_86_pick_first_leaf_default.html.

A timeline model of the first connection pass of gRPC Java's `pick_first` policy as written in the v1.86.0 sources of `PickFirstLoadBalancerProvider` and `PickFirstLeafLoadBalancer`: duplicate-address removal, serial attempts in list order (the 1.86.0 default), and, when `GRPC_PF_USE_HAPPY_EYEBALLS=true`, address-family interleaving with a new attempt every 250 ms while earlier attempts continue. Three synthetic scenarios: an IPv6 path that times out, a refused first address with a duplicate, and every address down.

Prerequisites: CPython 3.11 or newer (tested with 3.13.5). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment.

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (timelines and traces; asserted by the tests). The connect timeout is an input of the model (20,000 ms in the scenarios), not a claim about gRPC's default.

Limitations: this is not gRPC. It models only the first pass; per-address backoff after the first pass, health checking, resolver behaviour, sticky TRANSIENT_FAILURE over time and sockets are not simulated. Verify real behaviour with your gRPC version and network. Views are my own and do not represent any employer, past or present.

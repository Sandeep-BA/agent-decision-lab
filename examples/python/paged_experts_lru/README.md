# Paged MoE experts: LRU residency, waves and the decode capture limit

**Author: Sandeep Belgavi**

A runnable companion to *SGLang 0.5.23 Paged Experts: Serving an MoE Model Larger Than GPU Memory*
(aicassindra.com, GPU). It simulates the residency rules documented for SGLang Paged Experts on synthetic routing:
K GPU slots per MoE layer that start holding experts 0 to K-1, waves of at most K experts with resident experts
first, least-recently-used eviction outside the wave, and one page-in per miss. Transfer time is paged bytes over
all layers divided by the link bandwidth.

**No GPU, model or SGLang code is used.** The implementation is written from the SGLang documentation and the
behaviour of `paged_experts/residency.py` at v0.5.23 (Apache-2.0); no code is copied. Sizes come from the
documented Qwen3-30B-A3B GPTQ int4 example; top_k 8 comes from the model config.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/paged_experts_lru/paged.py examples/python/paged_experts_lru/fixtures/qwen3_30b_a3b_int4.json
python -m unittest discover -s examples/python/paged_experts_lru -p "test_*.py"
```

## Expected output

`expected_output.json` holds every run (seed 7). In short:

| Run | Decode miss rate | Transfer per decode step | Prefill paged | Decode captured |
| --- | --- | --- | --- | --- |
| default (locality 0.7, skew 0.6) | 5.5% | 1.03 ms | 4.2 GB | yes |
| no locality | 19.4% | 3.63 ms | 4.2 GB | yes |
| uniform routing | 26.8% | 5.0 ms | 4.2 GB | yes |
| K = 128 | 0% | 0 ms | 0 GB | yes |
| K = 26, four requests | 27.6% | 17.68 ms | 11.9 GB | no; 146 of 200 steps need two waves |
| 25 GB/s | 5.5% | 2.05 ms | 4.2 GB | yes |

Fixed by the documented sizes: 10.73 GB of expert slots on the GPU at K = 92, 14.93 GB of pinned host memory and
a capture limit of 92 // 8 = 11 concurrent requests. The interactive lab on aicassindra.com applies the same rules
with a different deterministic random source, so its exact percentages differ slightly; the tests here check
the relationships (uniform routing misses about 1 - K/E, locality lowers misses, bandwidth halves time) rather
than one random draw.

## Limitations

Routing is synthetic: real models route by content and layers differ from each other, while the simulator treats
all layers as identical. Kernel time, copy and compute overlap, the KV cache, CUDA graph replay cost and the
pinned-memory limit are not modelled. The transfer time is a calculation from an assumed bandwidth, not a
measurement; the throughput numbers in the article are the pull-request author's measurements.

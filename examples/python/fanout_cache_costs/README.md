# Prompt cache costs for parallel sub-agents

**Author: Sandeep Belgavi**

Companion to *Parallel Agent Fan-Out Misses the Prompt Cache*. Computes the cost of the shared prefix under three patterns and shows, offline, the warm-up order.

## Prerequisites
Python 3.11 or newer; standard library only. No API key is needed; nothing calls a provider.

## Commands
```
python examples/python/fanout_cache_costs/fanout.py
python -m unittest discover -s examples/python/fanout_cache_costs -p "test_*.py"
```

## Expected output
```
{'no_cache': 320000, 'simultaneous': 400000.0, 'warmed': 78000}
```

## Limits
The figures are arithmetic from published multipliers on the read date, and cost units of base input tokens only. Check the current price table and your provider's usage fields.

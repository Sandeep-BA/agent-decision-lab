"""Per-run arithmetic for the tool-definition part of agent requests. Author: Sandeep Belgavi.

Every request in an agent run resends the tool definitions plus the provider's tool-use system
prompt. The result is expressed in input-token equivalents (uncached input = 1.0), so no prices
are hard-coded. Multipliers are parameters: on the Claude API a 5-minute cache write is 1.25x
and a cache read 0.1x of base input (0.05x on some models), per Anthropic's prompt-caching page."""
from __future__ import annotations


def run_cost(tool_tokens, overhead, steps, cached=False, write_mult=1.25, read_mult=0.1, invalidations=0):
    """Token equivalents for the tool prefix over `steps` requests. `invalidations` counts mid-run
    changes to the tool list; each one turns the next request into a fresh cache write."""
    prefix = tool_tokens + overhead
    if steps < 1:
        raise ValueError('steps must be at least 1')
    if not cached:
        return prefix * steps
    writes = min(steps, 1 + invalidations)
    return prefix * (writes * write_mult + (steps - writes) * read_mult)


def deferred_prefix(always_loaded_tokens, search_tool_tokens, overhead):
    """Prefix when most tools are deferred behind a search tool: only the non-deferred ones remain."""
    return always_loaded_tokens + search_tool_tokens + overhead


if __name__ == '__main__':
    for label, t in (('concise', 1327), ('verbose', 3378)):
        print('%-8s 12 steps uncached %6.0f  cached %6.0f  cached with one tool-list change %6.0f' % (
            label, run_cost(t, 286, 12), run_cost(t, 286, 12, cached=True), run_cost(t, 286, 12, cached=True, invalidations=1)))

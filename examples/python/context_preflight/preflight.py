"""Author: Sandeep Belgavi. Check that an agent's next request fits before sending it, and shrink it in a fixed order.

Budget = context window - max output tokens - safety margin. Counting is injected: production code passes the
provider's token counting call (for example Anthropic's POST /v1/messages/count_tokens, Gemini's countTokens or
OpenAI's POST /responses/input_tokens). The offline demo uses `approx_count`, a rough 4-characters-per-token
estimate that is NOT any provider's tokenizer. Drop order: clear old tool results to a stub, then remove the
oldest whole turns, never the system prompt, tool definitions or the latest user message; if it still does not
fit, refuse to send.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Callable

Counter = Callable[[dict], int]


def approx_count(request: dict) -> int:
    """Rough offline estimate: characters of the JSON body / 4. Use the provider's counter in production."""
    return len(json.dumps(request, ensure_ascii=False)) // 4


class ContextBudgetError(RuntimeError):
    pass


@dataclass
class Plan:
    budget: int
    before: int
    after: int
    actions: list[str] = field(default_factory=list)


def budget_for(window: int, max_output: int, margin_pct: int = 5) -> int:
    return window - max_output - window * margin_pct // 100


def fit(request: dict, window: int, max_output: int, count: Counter = approx_count, keep_turns: int = 2,
        margin_pct: int = 5) -> tuple[dict, Plan]:
    req = copy.deepcopy(request)
    budget = budget_for(window, max_output, margin_pct)
    plan = Plan(budget, count(req), 0)
    msgs = req['messages']
    # 1. Clear tool results older than the last `keep_turns` user turns, oldest first.
    user_idx = [i for i, m in enumerate(msgs) if m['role'] == 'user' and isinstance(m['content'], str)]
    protect_from = user_idx[-keep_turns] if len(user_idx) >= keep_turns else 0
    for i, m in enumerate(msgs[:protect_from]):
        if count(req) <= budget:
            break
        if m['role'] == 'tool' and not m.get('cleared'):
            plan.actions.append('cleared tool result %s (%d chars)' % (m['id'], len(m['content'])))
            m['content'] = '[result %s cleared to fit the context; call the tool again if needed]' % m['id']
            m['cleared'] = True
    # 2. Remove whole old turns (a user message and everything up to the next user message).
    while count(req) > budget:
        starts = [i for i, m in enumerate(msgs) if m['role'] == 'user' and isinstance(m['content'], str)]
        if len(starts) <= keep_turns:
            break
        end = starts[1]
        plan.actions.append('removed turn starting %r (%d messages)' % (msgs[0]['content'][:40], end))
        del msgs[:end]
    plan.after = count(req)
    if plan.after > budget:
        raise ContextBudgetError('request needs %d tokens, budget is %d after removing everything removable'
                                 % (plan.after, budget))
    return req, plan


def classify_provider_error(status: int, body: dict) -> str:
    """Map a provider's 4xx to an action. Patterns are deliberately narrow; extend from your own logs."""
    text = json.dumps(body).lower()
    if status == 413:
        return 'request bytes too large: shrink attachments, do not retry unchanged'
    if status == 400 and ('prompt is too long' in text or 'context window' in text or 'context length' in text):
        return 'context overflow: re-run fit() with a smaller budget, do not retry unchanged'
    if status == 429:
        return 'rate limited: back off and retry the same request'
    return 'other client error: do not retry unchanged'


def fixture() -> dict:
    msgs = []
    for n in range(1, 7):
        msgs.append({'role': 'user', 'content': 'CASE-61%02d: customer Dinky asks about order %d' % (n, n)})
        msgs.append({'role': 'assistant', 'content': 'Looking up order %d.' % n})
        msgs.append({'role': 'tool', 'id': 'lookup-%d' % n, 'content': 'row,' * 1500})
        msgs.append({'role': 'assistant', 'content': 'Order %d shipped; refund window open.' % n})
    return {'system': 'You are the returns assistant for Belgavi\'s Book Store.',
            'tools': [{'name': 'lookup_order', 'description': 'Look up an order by number', 'input_schema': {'type': 'object'}}],
            'messages': msgs}


if __name__ == '__main__':
    req = fixture()
    print('approx tokens before:', approx_count(req))
    out, plan = fit(req, window=8000, max_output=1500)
    print('budget', plan.budget, 'before', plan.before, 'after', plan.after)
    for a in plan.actions:
        print(' -', a)
    try:
        fit(req, window=3000, max_output=1500)
    except ContextBudgetError as e:
        print('refused:', e)
    print(classify_provider_error(400, {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'prompt is too long'}}))

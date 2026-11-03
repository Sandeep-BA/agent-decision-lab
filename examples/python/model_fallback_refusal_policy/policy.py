"""Refusal fallback policy for pydantic-ai ModelFallback, pinned by tests.

Author: Sandeep Belgavi

Two FunctionModel instances stand in for a primary and a backup model, so no
provider is called. The primary refuses (finish_reason="content_filter"), with
or without text; the backup answers. Each scenario records which models were
called and what the run produced, under the library default and under an
explicit fallback_on=(ModelAPIError,) policy.
"""
from __future__ import annotations

import os

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.capabilities import ModelFallback  # noqa: E402
from pydantic_ai.exceptions import (  # noqa: E402
    ContentFilterError,
    ModelAPIError,
    ModelQuotaExceededError,
    ModelRateLimitError,
)
from pydantic_ai.messages import ModelResponse, TextPart  # noqa: E402
from pydantic_ai.models.function import FunctionModel  # noqa: E402

PROMPT = "Start a return for BK-1044, the cover is torn."
BACKUP_ANSWER = "Return label sent for order BK-1044."

# Explicit policies. Name the policy in code instead of relying on a default.
REFUSALS_FALL_BACK = (ModelAPIError, ContentFilterError)  # the 2.65.0 default
REFUSALS_STOP = (ModelAPIError,)  # the pre-2.65.0 default


def refusal(with_text: bool) -> ModelResponse:
    parts = [TextPart("I cannot help with that.")] if with_text else []
    return ModelResponse(parts=parts, finish_reason="content_filter", model_name="primary")


def run_scenario(refusal_has_text: bool, fallback_on=None) -> dict:
    """Run one agent request. fallback_on=None uses the installed library default."""
    calls: list[str] = []

    def primary(messages, info):
        calls.append("primary")
        return refusal(refusal_has_text)

    def backup(messages, info):
        calls.append("backup")
        return ModelResponse(parts=[TextPart(BACKUP_ANSWER)], model_name="backup")

    kwargs = {} if fallback_on is None else {"fallback_on": fallback_on}
    agent = Agent(FunctionModel(primary), capabilities=[ModelFallback(FunctionModel(backup), **kwargs)])
    try:
        output, error = agent.run_sync(PROMPT).output, None
    except ContentFilterError as exc:
        output, error = None, type(exc).__name__
    return {"calls": calls, "output": output, "error": error}


def quota_is_rate_limit() -> bool:
    return issubclass(ModelQuotaExceededError, ModelRateLimitError)


def main() -> None:
    import pydantic_ai

    print(f"pydantic-ai {pydantic_ai.__version__}")
    for label, policy in (("default", None), ("refusals_stop", REFUSALS_STOP)):
        for has_text in (True, False):
            r = run_scenario(has_text, policy)
            kind = "refusal+text " if has_text else "refusal empty"
            print(f"{label:<13} {kind} calls={r['calls']} output={r['output']!r} error={r['error']}")
    print(f"ModelQuotaExceededError is a ModelRateLimitError: {quota_is_rate_limit()}")


if __name__ == "__main__":
    main()

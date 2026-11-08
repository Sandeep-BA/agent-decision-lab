# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""ADK Python 2.14 passes Enum tool arguments as members. Normalise once at the top of a tool.

`run_probe()` needs google-adk installed (see requirements.txt); `parse_reason` does not.
"""
import asyncio
import enum


class Reason(enum.Enum):
    DAMAGED = "damaged"
    LATE = "late"


class Channel(str, enum.Enum):
    WEB = "web"
    PHONE = "phone"


def parse_reason(raw):
    if isinstance(raw, Reason):
        return raw
    try:
        return Reason(raw)
    except ValueError as err:
        raise ValueError(f"unknown reason: {raw!r}") from err


def refund_case(case_id: str, reason: Reason, channel: Channel) -> dict:
    """Record a refund for a help-desk case."""
    return {"case_id": case_id, "reason_type": type(reason).__name__, "reason_eq": reason == "damaged", "channel_eq": channel == "web"}


async def run_probe():
    from unittest.mock import MagicMock
    from google.adk.tools import FunctionTool
    from google.adk.tools.tool_context import ToolContext
    tool = FunctionTool(refund_case)
    return await tool.run_async(args={"case_id": "CASE-6101", "reason": "damaged", "channel": "web"},
                                tool_context=MagicMock(spec=ToolContext))


if __name__ == "__main__":
    print(asyncio.run(run_probe()))

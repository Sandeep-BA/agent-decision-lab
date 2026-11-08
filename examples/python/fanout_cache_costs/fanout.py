# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""Cost of a shared prompt prefix across a sub-agent fan-out, and an offline warm-up pattern.

Multipliers are the published Anthropic 5-minute cache figures on the read date: write 1.25x base input, read 0.1x.
Only arithmetic; no provider is called.
"""
import asyncio
from dataclasses import dataclass, field


def cost(prefix_tokens, agents, write_mult=1.25, read_mult=0.1):
    no_cache = agents * prefix_tokens
    simultaneous = agents * prefix_tokens * write_mult
    warmed = prefix_tokens * write_mult + (agents - 1) * prefix_tokens * read_mult
    return {"no_cache": no_cache, "simultaneous": simultaneous, "warmed": round(warmed)}


@dataclass
class FakeStream:
    name: str
    first_at: float
    total: float
    log: list
    released: asyncio.Event = field(default_factory=asyncio.Event)

    async def run(self):
        self.log.append(f"start {self.name}")
        await asyncio.sleep(self.first_at)
        self.released.set()
        self.log.append(f"first-event {self.name}")
        await asyncio.sleep(self.total - self.first_at)
        self.log.append(f"done {self.name}")
        return self.name


async def fan_out(agents):
    head, rest = agents[0], agents[1:]
    first = asyncio.create_task(head.run())
    await head.released.wait()
    others = [asyncio.create_task(a.run()) for a in rest]
    return await asyncio.gather(first, *others)


if __name__ == "__main__":
    print(cost(40000, 8))

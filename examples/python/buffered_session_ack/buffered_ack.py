"""When is an ADK turn durable? Author: Sandeep Belgavi.

Uses the real google-adk 2.15.0 BufferedSessionService (experimental) over an
InMemorySessionService subclass that adds a fixed delay per stored event and
can fail one chosen event. No model is called and no Runner is used: the
script appends four synthetic events of one help-desk turn for CASE-9101 at
the fictional Belgavi's Book Store, the way a runner would, and records what
the wrapped store holds at the moment each acknowledgement policy would
answer the client.
"""
import asyncio
import time

from google.adk.errors import SessionPersistenceError
from google.adk.events import Event
from google.adk.sessions import BufferedSessionService, InMemorySessionService
from google.genai import types

APP, USER, SID = 'bookstore_helpdesk', 'geetha', 'CASE-9101'
TEXTS = [('user', 'Where is my refund for order 4417?'),
         ('refund_agent', 'Looking up order 4417.'),
         ('refund_agent', 'Refund of 499 rupees was issued on 18 November.'),
         ('refund_agent', 'Anything else, Geetha?')]


class SlowStore(InMemorySessionService):
    """Stores each event after `delay` seconds; the `fail_at`-th stored event raises."""

    def __init__(self, delay=0.05, fail_at=None):
        super().__init__()
        self.delay, self.fail_at, self.calls = delay, fail_at, 0

    async def append_event(self, session, event):
        self.calls += 1
        await asyncio.sleep(self.delay)
        if self.fail_at == self.calls:
            raise ConnectionError(f'store unavailable on write {self.calls}')
        return await super().append_event(session, event)

    def stored(self):
        s = self.sessions.get(APP, {}).get(USER, {}).get(SID)
        return 0 if s is None else len(s.events)


def event(i):
    author, text = TEXTS[i]
    return Event(author=author, invocation_id='inv-1',
                 content=types.Content(role='user' if author == 'user' else 'model', parts=[types.Part(text=text)]))


async def turn(policy, delay=0.05, fail_at=None):
    store = SlowStore(delay, fail_at)
    service = BufferedSessionService(store)
    session = await service.create_session(app_name=APP, user_id=USER, session_id=SID)
    t0 = time.perf_counter()
    for i in range(len(TEXTS)):
        await service.append_event(session, event(i))
    result = {'policy': policy, 'fail_at': fail_at, 'events_in_session_object': len(session.events)}
    error = None
    if policy == 'flush_then_ack':
        try:
            await service.flush_session(app_name=APP, user_id=USER, session_id=SID)
        except SessionPersistenceError as e:
            error = e
    result['ack_ms'] = round((time.perf_counter() - t0) * 1000)
    result['stored_at_ack'] = store.stored()
    result['ack'] = 'error' if error else 'done'
    if error:
        result['error'] = type(error).__name__
        result['cause'] = repr(error.__cause__)
    try:
        await service.aclose()
        result['aclose'] = 'ok'
    except SessionPersistenceError as e:
        result['aclose'] = 'SessionPersistenceError: ' + repr(e.__cause__)
    result['stored_after_close'] = store.stored()
    return result


async def main_async():
    await turn('ack_after_append')  # warm-up: first use imports and logs a feature warning
    rows = [await turn('ack_after_append'), await turn('flush_then_ack'),
            await turn('ack_after_append', fail_at=3), await turn('flush_then_ack', fail_at=3)]
    for r in rows:
        print(r)
    return rows


def main():
    import google.adk
    print('google-adk', google.adk.__version__)
    asyncio.run(main_async())


if __name__ == '__main__':
    main()

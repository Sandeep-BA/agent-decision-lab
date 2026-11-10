# Shared work queue: strict priority, aging and weighted lanes

**Author: Sandeep Belgavi**

A runnable companion to *When Agents Share a Work Queue With People: Priority Lanes, Aging and Starvation* (aicassindra.com). A one-worker, one-item-per-tick model of a help-desk queue where agent items arrive at two per tick with priority 5 and one human case CASE-1001 waits with priority 3.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`flood_fixture()` in `lanes.py`: CASE-1001 at tick 0 and forty agent items over twenty ticks.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Four tests pass. Strict priority never starts CASE-1001 in twenty ticks; aging of one point per tick starts it at tick 4; weighted lanes (human 1, agent 3) start it at tick 2. Every policy completes twenty items.

## Limitations

One worker, unit service time, no preemption and no deadlines. Real queues have variable service times, many workers and items that change priority. This is a scheduling model, not a queue product.

Views are my own and do not represent any employer, past or present.

# EnvironmentScope initialize locks on a timeline

**Author: Sandeep Belgavi**

A runnable companion to *ADK Python 2.15.0 Locks Sandbox Initialization per Session, User or Environment* (aicassindra.com). A discrete-time model of the initialize lock keys ADK Python 2.15.0 uses for SHARED, USER and SESSION scopes, the close gate that waits for in-flight calls and holds new ones, and two cases the scope does not protect: a lock narrower than the resource, and two processes.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Five tool calls from Jenya, Geetha and Tanishka over four sessions in one process; a cold sandbox start takes 8 s, a warm initialize 0.1 s; a close at 3 s; one session reaching two processes.

## Commands

From this directory:

```
python scope_sim.py
python -m unittest -v
```

## Expected output

SHARED: waits 0, 7.5, 15.0, 14.6, 22.1 s. USER: Geetha's second session waits 6.5 s. SESSION: only the second call in Jenya's session waits (7.0 s). SESSION scope over a per-user sandbox creates it twice. Close requested at 3 s runs 10-11 s; a call at 4 s starts cold at 11 s. Two processes create one session's sandbox twice. 7 tests pass.

## Limitations

Model, not ADK code. Lock waiters are served first come, first served; ADK polls its locks and does not guarantee order. Durations are assumed.

Views are my own and do not represent any employer, past or present.

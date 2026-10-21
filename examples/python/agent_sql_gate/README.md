# Agent SQL gate: a capability boundary built from SQLite hooks

**Author: Sandeep Belgavi**

A runnable companion to *Letting an Agent Query an Existing Database: Read-Only Roles, Row-Level
Security, Settings an Agent Can Override and a Curated View Layer* (aicassindra.com, agents).
Agent-generated SQL is run through a gate that lives inside the SQLite engine:

- the connection is opened read-only (`mode=ro`);
- an authorizer callback (`Connection.set_authorizer`) allows `SELECT`, reads of five named columns of
  one table, reads of CTE columns, and a short list of functions; it denies writes, `ATTACH`,
  `PRAGMA`, other tables and extension loading;
- a progress handler (`Connection.set_progress_handler`) aborts any statement that runs past an
  instruction budget;
- the agent connects to a **per-tenant replica** that holds only its tenant's rows.

The example also keeps a weaker gate, `view_source_authorizer`, that lets a tenant view read its base
table by trusting the authorizer's fifth argument (the inner-most view responsible for a read).
SQLite puts a common table expression's name in that argument too, so
`WITH refunds_view AS (SELECT * FROM refunds) SELECT ...` passes the weak gate and returns every
tenant's rows. The tests pin that bypass down so it stays visible.

## Prerequisites

- Python 3.11 or newer. Standard library only (`sqlite3`, `json`, `argparse`, `unittest`).
- No network, no database server, no model provider, no credentials. `.env.example` documents that
  nothing is read from the environment.

## Sample input

`fixtures/agent_statements.json` holds ten statements an agent might produce. The application
database built by `build_fixture` has refunds for tenants 42 and 77, a payments table with card
digits, and a `refunds_view` that filters tenant 42 in its body.

## Commands

From the repository root:

```sh
python examples/python/agent_sql_gate/gate.py
python -m unittest discover -s examples/python/agent_sql_gate -p "test_*.py"
```

`gate.py` writes `app.db` and `tenant42.db` into `examples/python/agent_sql_gate/out/` (ignored by git).

## Expected output (verified with Python 3.13, SQLite 3.49.1)

```
replica rows for tenant 42: 3
== view-source gate on the application database
  ALLOWED  totals for the tenant: [(3, 4500)]
  ALLOWED  group by reason: [('damaged item', 1), ('duplicate charge', 1), ('late delivery', 1)]
  REFUSED  base table: access to refunds.id is prohibited
  REFUSED  another table: access to payments.card_last4 is prohibited
  REFUSED  write: not authorized
  REFUSED  attach: not authorized
  REFUSED  two statements: more than one statement
  REFUSED  extension loading: not authorized to use function: load_extension
  ALLOWED  CTE named like the view: [(14400,)]
  REFUSED  runaway recursive CTE: interrupted: instruction budget exhausted
== strict gate on the tenant replica
  ALLOWED  totals for the tenant: [(3, 4500)]
  ALLOWED  group by reason: [('damaged item', 1), ('duplicate charge', 1), ('late delivery', 1)]
  REFUSED  base table: no such table: refunds
  REFUSED  another table: no such table: payments
  REFUSED  write: no such table: refunds
  REFUSED  attach: not authorized
  REFUSED  two statements: more than one statement
  REFUSED  extension loading: not authorized to use function: load_extension
  REFUSED  CTE named like the view: no such table: refunds
  REFUSED  runaway recursive CTE: interrupted: instruction budget exhausted
```

The line to read is `CTE named like the view`: 14,400 cents is both tenants' refunds (4,500 + 9,900).

## Tests

`test_gate.py` (9 tests): the replica holds only tenant 42; the allowed aggregate returns 3 rows and
4,500 cents; reads of other tables, writes, `ATTACH`, `PRAGMA`, DDL and `load_extension` are refused;
the read-only connection refuses a delete even without the authorizer; a runaway recursive CTE is
interrupted while a small one is allowed; the view-source gate leaks 14,400 cents through a CTE named
like the view, and the strict gate on the replica refuses it.

## Limitations

- SQLite has no roles or row-level security. The replica stands in for PostgreSQL row-level security
  plus `security_invoker` views; it is a teaching substitute, not a recommendation to copy tenants
  into files.
- The multiple-statement check is a plain semicolon test and refuses a semicolon inside a string
  literal. `sqlite3` also refuses multiple statements in `execute()` on its own.
- The instruction budget (`2,000` callbacks of `1,000` virtual machine instructions) is a demo value;
  measure your own queries before choosing one, and keep a wall-clock deadline in the caller.
- Authorizer behaviour was verified with SQLite 3.49.1; rerun the tests when the SQLite version changes.

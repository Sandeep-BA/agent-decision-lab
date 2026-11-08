# Watching a generic plan take over

**Author: Sandeep Belgavi**

Companion to *The Sixth Execution Got Slower*. Prints which plan each of eight executions used, on skewed synthetic orders.

## Prerequisites
Python 3.11 or newer, `pip install -r examples/python/plan_flip_pg/requirements.txt`, and a throwaway PostgreSQL 14+ database (the script **drops** a table called `orders`).

## Commands
```
python -m unittest discover -s examples/python/plan_flip_pg -p "test_*.py"
PG_DSN="host=127.0.0.1 port=5432 user=postgres dbname=throwaway" python examples/python/plan_flip_pg/plan_flip.py
```

## Expected output
Executions 1 to 5 report `custom`; from execution 6 onward the plan is `generic` and the time rises for small stores; `generic_plans` and `custom_plans` appear at the end. Timings depend on your machine.

## Limits
A synthetic table on one machine; compare your own data and PostgreSQL version.

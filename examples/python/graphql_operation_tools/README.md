# graphql_operation_tools

**Author: Sandeep Belgavi**

Companion to the guide *Let Agents Call a GraphQL API Through Persisted Operations* on aicassindra.com.

The agent never writes GraphQL. Each registered operation becomes one tool with typed variables. The
gateway checks the variables, estimates the cost from the operation's declared list sizes, charges a
per-run budget, sends only the registered document, and turns a GraphQL response into a tool result
that marks failed fields as unavailable instead of empty.

- `operation_tools.py`: the operation registry (`order_status_v1`, `customer_orders_v1`), variable
  checks, `RunBudget`, `null_prefix()` (a field error on a non-null field nulls its nearest nullable
  parent, so that parent is what is missing) and `to_tool_result()`.
- `responses.json`: synthetic responses for Belgavi's Book Store: complete, a failed nullable field, an
  error that propagated to the parent, and a request error with no data.
- `demo.py`: six tool calls, including an ad-hoc query and a malformed order id.

## Prerequisites

Python 3.11 or newer, standard library only. Tested with Python 3.13.5. No GraphQL server is called; the
transport is a function you replace with an HTTP POST to your gateway.

## Run

```
python demo.py
python -m unittest -v
```

Expected output is in `expected_output.txt`. It ends with:

```
budget spent 217 of 300: [('order_status_v1', 3), ('order_status_v1', 3), ('customer_orders_v1', 211)]
```

## Limitations

- The cost of each operation is a hand-written function of its variables, mirroring the list sizes in
  the document. A real gateway should derive it from the schema (or use the server's own cost analysis)
  and test that the two agree.
- No GraphQL parsing, validation or execution happens here; the responses are recorded fixtures.
- The budget lives in memory for one run. A service with several replicas needs it in shared storage.

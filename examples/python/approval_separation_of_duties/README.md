# Separation of duties with agents in an approval chain

**Author: Sandeep Belgavi**

A runnable companion to *Separation of Duties When an Agent Joins an Approval Chain* (aicassindra.com). Resolves every requester, editor and approver to the accountable person behind it, then applies maker-checker rules in a fixed order: the checker is a person with the role and limit, and is neither the accountable requester nor an editor of the payload.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Six synthetic refund approvals in `CASES` (CASE-5101 to CASE-5106). Run `python sod.py` to print each decision.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Five tests pass. Exactly one of the six cases is allowed: an agent drafting for Tanishka and Geetha approving. An agent acting for Geetha cannot have Geetha approve, editing the payload makes Geetha a maker, an agent cannot approve, an agent with no owner cannot request, and Jenya cannot approve above her limit.

## Limitations

Rules only. No identity provider, token validation, delegation chains longer than one hop or audit storage. Role names and limits are illustrative.

Views are my own and do not represent any employer, past or present.

"""A return-assessment endpoint that answers 202 Accepted with a job resource instead of waiting for an agent.

Author: Sandeep Belgavi. Standard library only (sqlite3 in memory). The agent is a scripted function and time
is simulated, so the guards can be tested exactly. Nothing calls a model or the network.

Guards shown:
- the job is created by a UNIQUE constraint on the Idempotency-Key, so a resent POST returns the same job;
- the store credit is keyed on the return id, so a job retried after a worker crash cannot pay twice;
- running jobs hold a lease; an expired lease puts the job back in the queue;
- every status response carries Retry-After.
"""
import json
import sqlite3
import sys

SCHEMA = """
CREATE TABLE jobs (job_id TEXT PRIMARY KEY, idem_key TEXT UNIQUE, return_id TEXT NOT NULL,
                   state TEXT NOT NULL, lease_until REAL, attempts INTEGER NOT NULL DEFAULT 0, result TEXT);
CREATE TABLE credits (return_id TEXT PRIMARY KEY, amount INTEGER NOT NULL);
"""
RETRY_AFTER = 5
LEASE = 60


def scripted_agent(return_id):
    """Stand-in for the agent: unopened books get full credit, everything else half."""
    return {"decision": "credit", "amount": 20 if return_id.endswith("U") else 10}


class Service:
    def __init__(self, idempotent_post=True):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA)
        self.idempotent_post, self.counter, self.now = idempotent_post, 0, 0.0

    def post(self, return_id, idem_key=None):
        """POST /return-assessments -> (status, body, headers)."""
        if self.idempotent_post and not idem_key:
            return 400, {"error": "Idempotency-Key is required"}, {}
        self.counter += 1
        job_id = "J-%04d" % self.counter
        key = idem_key if self.idempotent_post else None
        self.db.execute("INSERT INTO jobs (job_id, idem_key, return_id, state) VALUES (?, ?, ?, 'queued') "
                        "ON CONFLICT (idem_key) DO NOTHING", (job_id, key, return_id))
        if key is not None:
            job_id, rid = self.db.execute("SELECT job_id, return_id FROM jobs WHERE idem_key = ?", (key,)).fetchone()
            if rid != return_id:
                return 422, {"error": "Idempotency-Key reused for another return"}, {}
        return 202, {"job_id": job_id, "state": "queued"}, {"Location": "/return-assessments/jobs/" + job_id,
                                                           "Retry-After": str(RETRY_AFTER)}

    def get(self, job_id):
        """GET /return-assessments/jobs/{id} -> (status, body, headers)."""
        row = self.db.execute("SELECT state, result FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return 404, {"error": "no such job"}, {}
        body = {"job_id": job_id, "state": row[0]}
        if row[1]:
            body["result"] = json.loads(row[1])
        headers = {} if row[0] in ("succeeded", "failed") else {"Retry-After": str(RETRY_AFTER)}
        return 200, body, headers

    def claim(self):
        """A worker claims one queued job, or one whose lease has expired."""
        row = self.db.execute("SELECT job_id, return_id FROM jobs WHERE state = 'queued' OR "
                              "(state = 'running' AND lease_until < ?) ORDER BY job_id LIMIT 1", (self.now,)).fetchone()
        if row:
            self.db.execute("UPDATE jobs SET state = 'running', lease_until = ?, attempts = attempts + 1 "
                            "WHERE job_id = ?", (self.now + LEASE, row[0]))
        return row

    def work(self, crash_before_finish=False):
        """Run one claimed job to completion; a crash leaves the credit issued and the job running."""
        row = self.claim()
        if not row:
            return None
        job_id, return_id = row
        decision = scripted_agent(return_id)
        self.db.execute("INSERT INTO credits (return_id, amount) VALUES (?, ?) ON CONFLICT (return_id) DO NOTHING",
                        (return_id, decision["amount"]))
        if crash_before_finish:
            return job_id
        self.db.execute("UPDATE jobs SET state = 'succeeded', result = ?, lease_until = NULL WHERE job_id = ?",
                        (json.dumps(decision), job_id))
        return job_id

    def credits_for(self, return_id):
        return self.db.execute("SELECT COUNT(*) FROM credits WHERE return_id = ?", (return_id,)).fetchone()[0]

    def jobs_for(self, return_id):
        return self.db.execute("SELECT COUNT(*) FROM jobs WHERE return_id = ?", (return_id,)).fetchone()[0]


def main(argv):
    out = {}
    s = Service()
    first = s.post("RET-1001U", "k-1001")
    resent = s.post("RET-1001U", "k-1001")          # the 202 was lost; the client sends the POST again
    s.work()
    out["with_key"] = {"same_job": first[1]["job_id"] == resent[1]["job_id"], "jobs": s.jobs_for("RET-1001U"),
                       "status": s.get(first[1]["job_id"])[1]}
    n = Service(idempotent_post=False)
    n.post("RET-1002")
    n.post("RET-1002")
    n.work()
    n.work()
    out["without_key"] = {"jobs": n.jobs_for("RET-1002"), "credits": n.credits_for("RET-1002")}
    c = Service()
    job = c.post("RET-1003", "k-1003")[1]["job_id"]
    c.work(crash_before_finish=True)
    c.now += LEASE + 1                               # the lease expires; another worker takes the job
    c.work()
    out["after_crash"] = {"credits": c.credits_for("RET-1003"), "status": c.get(job)[1]["state"],
                          "attempts": c.db.execute("SELECT attempts FROM jobs WHERE job_id = ?", (job,)).fetchone()[0]}
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main(sys.argv[1:])

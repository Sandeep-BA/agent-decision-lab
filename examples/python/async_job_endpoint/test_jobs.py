"""Tests for the async job endpoint example. Author: Sandeep Belgavi."""
import unittest

from jobs import LEASE, RETRY_AFTER, Service


class AsyncJobEndpoint(unittest.TestCase):
    def test_post_answers_202_with_location_and_retry_after(self):
        status, body, headers = Service().post("RET-1", "k-1")
        self.assertEqual(status, 202)
        self.assertEqual(headers["Location"], "/return-assessments/jobs/" + body["job_id"])
        self.assertEqual(headers["Retry-After"], str(RETRY_AFTER))

    def test_resent_post_with_the_same_key_returns_the_same_job(self):
        s = Service()
        a, b = s.post("RET-1", "k-1"), s.post("RET-1", "k-1")
        self.assertEqual(a[1]["job_id"], b[1]["job_id"])
        self.assertEqual(s.jobs_for("RET-1"), 1)

    def test_key_reused_for_another_return_is_refused(self):
        s = Service()
        s.post("RET-1", "k-1")
        self.assertEqual(s.post("RET-2", "k-1")[0], 422)

    def test_missing_key_is_refused(self):
        self.assertEqual(Service().post("RET-1")[0], 400)

    def test_without_a_post_key_two_jobs_run_but_the_credit_key_still_pays_once(self):
        s = Service(idempotent_post=False)
        s.post("RET-2")
        s.post("RET-2")
        s.work()
        s.work()
        self.assertEqual(s.jobs_for("RET-2"), 2)
        self.assertEqual(s.credits_for("RET-2"), 1)

    def test_status_keeps_retry_after_until_done_then_returns_the_result(self):
        s = Service()
        job = s.post("RET-3U", "k-3")[1]["job_id"]
        self.assertEqual(s.get(job)[2], {"Retry-After": str(RETRY_AFTER)})
        s.work()
        status, body, headers = s.get(job)
        self.assertEqual((status, body["state"], body["result"]["amount"], headers), (200, "succeeded", 20, {}))

    def test_crashed_worker_lease_expires_and_the_retry_does_not_pay_twice(self):
        s = Service()
        job = s.post("RET-4", "k-4")[1]["job_id"]
        s.work(crash_before_finish=True)
        self.assertIsNone(s.work())                 # lease still held: nothing to claim
        s.now += LEASE + 1
        s.work()
        self.assertEqual(s.get(job)[1]["state"], "succeeded")
        self.assertEqual(s.credits_for("RET-4"), 1)


if __name__ == "__main__":
    unittest.main()

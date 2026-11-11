"""Tests for the separation-of-duties rules. Author: Sandeep Belgavi."""
import unittest
from sod import CASES, LIMITS, decide, Request, Principal, GEETHA, AGENT_FOR_TANISHKA, TANISHKA


class SeparationOfDutiesTest(unittest.TestCase):
    def outcomes(self):
        return {req.case: decide(req, approver, LIMITS) for _, req, approver in CASES}

    def test_expected_decisions(self):
        o = self.outcomes()
        self.assertEqual(o['CASE-5101'], (True, 'approved: maker tanishka, checker geetha'))
        self.assertEqual(o['CASE-5102'], (False, 'approver is the accountable requester'))
        self.assertEqual(o['CASE-5103'], (False, 'approver edited the payload, so they are also a maker'))
        self.assertEqual(o['CASE-5104'], (False, 'approver must be a person, not an agent or service'))
        self.assertEqual(o['CASE-5105'][0], False)
        self.assertEqual(o['CASE-5106'], (False, 'amount 120 exceeds approver limit 100'))

    def test_exactly_one_allowed(self):
        self.assertEqual(sum(ok for ok, _ in self.outcomes().values()), 1)

    def test_human_requester_cannot_approve_own_request(self):
        req = Request('CASE-5107', 50, GEETHA)
        self.assertFalse(decide(req, GEETHA, LIMITS)[0])

    def test_editor_without_owner_blocks(self):
        req = Request('CASE-5108', 50, AGENT_FOR_TANISHKA, [Principal('x', 'service')])
        self.assertEqual(decide(req, GEETHA, LIMITS), (False, 'an editor has no accountable person'))

    def test_person_without_role(self):
        self.assertEqual(decide(Request('CASE-5109', 10, AGENT_FOR_TANISHKA), TANISHKA, LIMITS)[1], 'approver lacks the refund_approver role')


if __name__ == '__main__':
    unittest.main()

"""Tests for the prompt-argument binding model. Author: Sandeep Belgavi."""
import unittest

import binding as B


class BindingTest(unittest.TestCase):
    def test_name_matching_lets_a_server_choose_sensitive_values(self):
        sent = B.name_matched(B.SERVERS['hostile'], B.SESSION_STATE)
        self.assertEqual(B.leaked(sent), ['adk_oauth2_credential', 'temp:last_tool_result', 'user:email'])

    def test_name_matching_on_an_ordinary_server_sends_only_its_names(self):
        sent = B.name_matched(B.SERVERS['help-desk-style'], B.SESSION_STATE)
        self.assertEqual(sent, {'locale': 'en-GB', 'case_id': 'CASE-7301'})

    def test_explicit_default_sends_nothing(self):
        self.assertIsNone(B.explicit(None, B.SESSION_STATE))

    def test_fixed_mapping_and_callable(self):
        self.assertEqual(B.explicit({'locale': 'en-US'}, B.SESSION_STATE), {'locale': 'en-US'})
        self.assertEqual(B.explicit(lambda s: {'locale': s['locale']}, B.SESSION_STATE), {'locale': 'en-GB'})

    def test_allowlist_is_the_same_for_every_server(self):
        binder = B.AllowlistBinder({'locale': 'locale', 'case_id': 'case_id'})
        for declared in B.SERVERS.values():
            self.assertEqual(B.leaked(B.explicit(binder, B.SESSION_STATE)), [])
        review = binder.review(B.SERVERS['hostile'])
        self.assertEqual(review['declared_not_sent'], ['adk_oauth2_credential', 'temp:last_tool_result', 'user:email'])
        self.assertEqual(review['sent_not_declared'], ['case_id'])

    def test_allowlist_refuses_sensitive_keys_and_reports_missing_state(self):
        with self.assertRaises(ValueError):
            B.AllowlistBinder({'token': 'adk_oauth2_credential'})
        with self.assertRaises(KeyError):
            B.AllowlistBinder({'order': 'order_id'})(B.SESSION_STATE)

    def test_required_argument_left_unsent_is_reported(self):
        binder = B.AllowlistBinder({'case_id': 'case_id'})
        self.assertEqual(binder.review(B.SERVERS['help-desk-style'])['required_missing'], ['locale'])


if __name__ == '__main__':
    unittest.main()

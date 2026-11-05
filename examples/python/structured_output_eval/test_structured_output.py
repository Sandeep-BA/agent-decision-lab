"""Offline tests over the recorded runs. Author: Sandeep Belgavi. Run: python -m unittest -v"""
import json, pathlib, unittest
import report
from grounding import ungrounded
from run_eval import score
from schema import problems

HERE = pathlib.Path(__file__).resolve().parent
CASES = report.CASES


def rec(name):
    return json.loads((HERE / 'recordings' / name).read_text(encoding='utf-8'))


class SchemaTest(unittest.TestCase):
    def test_validator(self):
        good = {'case_type': 'refund', 'order_id': None, 'amount_inr': 649, 'wants_person': False}
        self.assertEqual(problems(good), [])
        self.assertIn('order_id pattern', problems(dict(good, order_id='bk-40622')))
        self.assertIn('case_type not in enum', problems(dict(good, case_type='complaint')))
        self.assertIn('amount_inr type', problems(dict(good, amount_inr=True)))
        self.assertIn('extra note', problems(dict(good, note='x')))


class GroundingTest(unittest.TestCase):
    def test_order_id_must_appear_in_the_text(self):
        text = 'My order bk 40622 came with pages missing.'
        self.assertEqual(ungrounded({'order_id': 'BK-40622', 'amount_inr': None}, text), [])
        self.assertEqual(ungrounded({'order_id': 'BK-00001', 'amount_inr': None}, text), ['order_id'])

    def test_amount_with_thousands_separator(self):
        self.assertEqual(ungrounded({'order_id': None, 'amount_inr': 1250}, 'refund of Rs 1,250'), [])
        self.assertEqual(ungrounded({'order_id': None, 'amount_inr': 125}, 'refund of Rs 1,250'), ['amount_inr'])


class RecordedRunTest(unittest.TestCase):
    def test_schema_mode_is_always_valid_but_not_always_right(self):
        for name, right in (('qwen2.5_0.5b-instruct.json', 3), ('qwen2.5_1.5b.json', 1)):
            t = score(CASES, rec(name)['outputs']['schema'])
            self.assertEqual((t['parsed'], t['valid'], t['all_correct']), (12, 12, right), name)

    def test_prompt_only_small_model_wraps_json_in_fences(self):
        r = rec('qwen2.5_0.5b-instruct.json')
        self.assertEqual(score(CASES, r['outputs']['prompt'])['parsed'], 0)
        self.assertTrue(r['outputs']['prompt']['c01'].startswith('```json'))

    def test_constraint_turns_a_detectable_bad_id_into_a_valid_looking_one(self):
        r = rec('qwen2.5_1.5b.json')
        self.assertEqual(report.wrong_ids(r, 'prompt')['schema_catches'], [('c06', 'BK-000125')])
        w = report.wrong_ids(r, 'schema')
        self.assertEqual(w['schema_catches'], [])
        self.assertIn(('c06', 'BK-00012'), w['grounding_catches'])
        self.assertEqual(len(w['grounding_catches']), 3)
        self.assertEqual(w['nobody_catches'], [])


if __name__ == '__main__':
    unittest.main()

"""Author: Sandeep Belgavi."""
import unittest
from recording_sink import Proposal, RecordingSink


class Sink(unittest.TestCase):
    def test_records_without_execution(self):
        sink = RecordingSink()
        self.assertEqual(sink.submit(Proposal('CASE-0001', 3, 'synthetic')), {'recorded': True, 'executed': False})
        self.assertEqual(len(sink.proposals), 1)

    def test_rejects_untyped_and_negative(self):
        sink = RecordingSink()
        with self.assertRaises(ValueError):
            sink.submit(Proposal('CASE-0002', -1, 'x'))
        with self.assertRaises(TypeError):
            sink.submit({'execute': True})
        self.assertEqual(sink.proposals, [])

    def test_module_exposes_no_effect_client(self):
        import recording_sink
        self.assertEqual([n for n in dir(recording_sink) if 'client' in n.lower() or 'execut' in n.lower()], [])


if __name__ == '__main__':
    unittest.main()

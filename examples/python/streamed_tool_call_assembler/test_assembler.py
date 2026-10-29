"""Tests for assembler.py. Author: Sandeep Belgavi."""
import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assembler as asm

A, B = json.dumps(asm.ARGS_A), json.dumps(asm.ARGS_B)


class AssemblerTest(unittest.TestCase):
    def test_every_two_piece_split_reassembles_identically(self):
        for pieces in asm.split_everywhere(A):
            acc = asm.ToolCallAccumulator()
            done = asm.feed_claude(asm.claude_stream(pieces, [B]), acc)
            self.assertEqual([p for _, p in done], [asm.ARGS_A, asm.ARGS_B])

    def test_escaped_unicode_split_inside_escape_sequence(self):
        escaped = json.dumps(asm.ARGS_A, ensure_ascii=True)
        i = escaped.index(r'\u2014') + 3             # split inside the six-character escape
        acc = asm.ToolCallAccumulator()
        done = asm.feed_openai(asm.openai_stream([escaped[:i], escaped[i:]], escaped), acc)
        call, parsed = done[0]
        self.assertEqual(parsed, asm.ARGS_A)
        self.assertNotIn('mismatch', call)

    def test_parallel_calls_are_keyed_by_index(self):
        acc = asm.ToolCallAccumulator()
        done = asm.feed_claude(asm.claude_stream(list(A), list(B)), acc)
        self.assertEqual({c['id']: p['amount'] for c, p in done}, {'toolu_A': 349.0, 'toolu_B': 25.0})

    def test_truncated_call_never_executes(self):
        truncated = A[:A.index('"note"') - 2]
        acc = asm.ToolCallAccumulator()
        (call_a, parsed_a), (call_b, parsed_b) = asm.feed_claude(asm.claude_stream([truncated], [B]), acc)
        verdict, result = asm.gate(call_a, parsed_a)
        self.assertEqual(verdict, 'error')
        self.assertTrue(result['is_error'])
        self.assertEqual(json.loads(result['content']), {'INVALID_JSON': truncated})
        self.assertEqual(asm.gate(call_b, parsed_b)[0], 'execute')

    def test_openai_done_event_overrides_and_flags_mismatch(self):
        acc = asm.ToolCallAccumulator()
        done = asm.feed_openai(asm.openai_stream([A[:20]], A), acc)   # lost fragments
        call, parsed = done[0]
        self.assertTrue(call['mismatch'])
        self.assertEqual(parsed, asm.ARGS_A)

    def test_gemini_assembles_on_completion(self):
        acc = asm.ToolCallAccumulator()
        done = asm.feed_gemini(asm.gemini_stream([A[:30], A[30:]]), acc)
        self.assertEqual(done[0][1], asm.ARGS_A)

    def test_gate_rejects_amount_above_order_total(self):
        args = dict(asm.ARGS_A, amount=5000.0)
        verdict, _ = asm.gate({'id': 'x', 'buf': json.dumps(args)}, args)
        self.assertEqual(verdict, 'error')

    def test_fragment_after_finish_is_refused(self):
        acc = asm.ToolCallAccumulator()
        acc.start(1, 'toolu_A', 'issue_refund')
        acc.finish(1)
        with self.assertRaises(ValueError):
            acc.fragment(1, '{}')


if __name__ == '__main__':
    unittest.main()

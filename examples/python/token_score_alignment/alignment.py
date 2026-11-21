"""Align generated tokens with their scores before summing likelihoods. Author: Sandeep Belgavi.

A pure-Python model of the bookkeeping around Hugging Face Transformers
`generate(..., output_scores=True, return_dict_in_generate=True)` and
`compute_transition_scores`. No model, tokenizer or torch is used: the
"scores" are synthetic log-probability tables over a six-token vocabulary.

Facts it mirrors (Transformers v5 source, generation/utils.py):
- `sequences` holds prompt plus generated tokens; `scores` has one entry per
  generation step, so generated positions are the LAST len(scores) columns.
- In greedy/sampling search a finished row keeps receiving the pad token, and
  without beam indices `compute_transition_scores` does not mask those steps.
- `scores` are processed (after temperature and filtering); `logits` are raw.
"""
import math

VOCAB = ['<pad>', '<eos>', 'refund', 'issued', 'for', 'CASE-7101']
PAD, EOS = 0, 1


def log_softmax(row):
    m = max(row)
    z = math.log(sum(math.exp(x - m) for x in row)) + m
    return [x - z for x in row]


# Two rows, left-padded prompts of padded width 4, five generation steps.
PROMPTS = [[PAD, 4, 5, 2], [4, 5, 2, 3]]
GENERATED = [[2, 3, 1, PAD, PAD],   # row 0 stops with <eos> at step 2
             [3, 4, 5, 2, 1]]       # row 1 runs all five steps
# Synthetic raw logits per step and row (6 vocabulary entries each).
RAW = [
    [[0.0, 0.1, 2.0, 0.5, 0.2, 0.1], [0.0, 0.2, 0.3, 2.2, 0.4, 0.1]],
    [[0.0, 0.3, 0.2, 1.9, 0.6, 0.1], [0.0, 0.1, 0.5, 0.3, 2.1, 0.2]],
    [[0.0, 2.4, 0.1, 0.2, 0.3, 0.1], [0.0, 0.2, 0.1, 0.4, 0.3, 2.0]],
    [[1.5, 0.0, 0.2, 0.1, 0.3, 0.1], [0.0, 0.3, 1.8, 0.2, 0.5, 0.1]],
    [[1.2, 0.0, 0.1, 0.3, 0.2, 0.2], [0.0, 2.1, 0.2, 0.3, 0.4, 0.1]],
]


def processed(temperature):
    return [[log_softmax([x / temperature for x in row]) for row in step] for step in RAW]


def sequences():
    return [p + g for p, g in zip(PROMPTS, GENERATED)]


def transition_scores(seqs, scores):
    """Like compute_transition_scores without beams: align to the last steps, gather, no masking."""
    steps = len(scores)
    out = []
    for r, seq in enumerate(seqs):
        tail = seq[len(seq) - steps:]
        out.append([scores[s][r][tok] for s, tok in enumerate(tail)])
    return out


def finished_mask(generated):
    """True for positions a row actually chose: up to and including its first <eos>."""
    mask = []
    for row in generated:
        live, m = True, []
        for tok in row:
            m.append(live)
            if tok == EOS:
                live = False
        mask.append(m)
    return mask


def sequence_logprob(seqs, scores, generated, masked=True):
    ts = transition_scores(seqs, scores)
    mask = finished_mask(generated) if masked else [[True] * len(r) for r in generated]
    return [sum(v for v, keep in zip(row, m) if keep) for row, m in zip(ts, mask)]


def per_row_prompt_slice(seqs, prompts):
    """The bug: slicing each row by its unpadded prompt length shifts left-padded rows."""
    return [seq[sum(1 for t in p if t != PAD):] for seq, p in zip(seqs, prompts)]


def check_comparable(a, b):
    """Refuse to compare traces that are not measured on the same scale."""
    problems = []
    for key in ('tokenizer_sha256', 'score_kind', 'temperature'):
        if a[key] != b[key]:
            problems.append(f"{key} differs: {a[key]} vs {b[key]}")
    if a['steps'] != len(a['scores']) or b['steps'] != len(b['scores']):
        problems.append('scores length does not match generated steps')
    return problems


def main():
    seqs, scores = sequences(), processed(1.0)
    print('steps', len(scores), 'sequence width', len(seqs[0]))
    naive = sequence_logprob(seqs, scores, GENERATED, masked=False)
    masked = sequence_logprob(seqs, scores, GENERATED, masked=True)
    print('row 0 log-prob unmasked %.4f masked %.4f' % (naive[0], masked[0]))
    print('row 1 log-prob unmasked %.4f masked %.4f' % (naive[1], masked[1]))
    shifted = per_row_prompt_slice(seqs, PROMPTS)
    print('per-row slice lengths', [len(x) for x in shifted], 'expected', [len(g) for g in GENERATED])
    hot = sequence_logprob(seqs, processed(0.7), GENERATED)
    print('row 1 at temperature 0.7: %.4f' % hot[1])
    a = {'tokenizer_sha256': 'aa11', 'score_kind': 'processed', 'temperature': 1.0, 'steps': 5, 'scores': scores}
    b = {'tokenizer_sha256': 'bb22', 'score_kind': 'processed', 'temperature': 0.7, 'steps': 5, 'scores': scores}
    print('comparable problems:', check_comparable(a, b))


if __name__ == '__main__':
    main()

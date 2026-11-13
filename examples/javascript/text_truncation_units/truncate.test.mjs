// Author: Sandeep Belgavi. node --test truncate.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { SAMPLES, byCodePoints, byGraphemes, byUtf16, byUtf8Bytes, forDisplay, hasLoneSurrogate, measure, naiveUtf8Bytes, report } from './truncate.mjs';

const fam = SAMPLES.family;

test('one family emoji is 8 UTF-16 units, 5 code points, 1 grapheme, 18 bytes', () => {
  assert.deepEqual(measure('\u{1F468}‍\u{1F469}‍\u{1F467}'), { utf16: 8, codePoints: 5, graphemes: 1, utf8Bytes: 18 });
});

test('UTF-16 slice can leave a lone surrogate', () => {
  assert.equal(hasLoneSurrogate(byUtf16(fam, 11)), true);
  assert.equal(hasLoneSurrogate(byCodePoints(fam, 11)), false);
});

test('code points never split a surrogate pair but do split a ZWJ sequence', () => {
  const r = report(fam, 'codePoints', 13);
  assert.equal(r.loneSurrogate, false);
  assert.equal(r.brokenLastCluster, true);
});

test('graphemes keep clusters whole', () => {
  assert.equal(byGraphemes(fam, 11), 'Order for \u{1F468}‍\u{1F469}‍\u{1F467}');
  assert.equal(byGraphemes(SAMPLES.flag, 10), 'Ships to \u{1F1EE}\u{1F1F3}');
  assert.equal(byGraphemes(SAMPLES.accent, 4), 'José');
});

test('code-point truncation drops a combining accent', () => {
  assert.equal(byCodePoints(SAMPLES.accent, 4), 'Jose');
});

test('byte budget is respected without replacement characters', () => {
  for (const n of [0, 5, 10, 11, 27, 28, 35]) {
    const out = byUtf8Bytes(fam, n);
    assert.ok(new TextEncoder().encode(out).length <= n);
    assert.equal(out.includes('�'), false);
  }
  assert.equal(byUtf8Bytes(fam, 28), 'Order for \u{1F468}‍\u{1F469}‍\u{1F467}');
});

test('cutting bytes then decoding produces U+FFFD', () => {
  assert.ok(naiveUtf8Bytes(fam, 12).includes('�'));
});

test('display truncation reserves room for the ellipsis', () => {
  assert.equal(forDisplay('abcdef', 4), 'abc…');
  assert.equal(forDisplay('abc', 4), 'abc');
  assert.equal(forDisplay(SAMPLES.flag, 11), 'Ships to \u{1F1EE}\u{1F1F3}…');
});

// Author: Sandeep Belgavi. Truncate text by four different units and report what breaks.
// Original example. Uses only the JavaScript standard library (Intl.Segmenter, TextEncoder).

const enc = new TextEncoder();
export const graphemes = (s) => [...new Intl.Segmenter('en', { granularity: 'grapheme' }).segment(s)].map((x) => x.segment);
export const measure = (s) => ({ utf16: s.length, codePoints: [...s].length, graphemes: graphemes(s).length, utf8Bytes: enc.encode(s).length });
export const hasLoneSurrogate = (s) => /\p{Surrogate}/u.test(s);

// Each function returns the longest prefix within `limit` units of its kind.
export function byUtf16(s, limit) { return s.slice(0, limit); }
export function byCodePoints(s, limit) { return [...s].slice(0, limit).join(''); }
export function byGraphemes(s, limit) { return graphemes(s).slice(0, limit).join(''); }
export function byUtf8Bytes(s, limit) {
  // Whole grapheme clusters whose UTF-8 encoding fits the byte budget.
  let out = '', used = 0;
  for (const g of graphemes(s)) {
    const n = enc.encode(g).length;
    if (used + n > limit) break;
    out += g; used += n;
  }
  return out;
}
export function naiveUtf8Bytes(s, limit) {
  // Cut the byte array, then decode: a split sequence becomes U+FFFD.
  return new TextDecoder().decode(enc.encode(s).slice(0, limit));
}
export const UNITS = { utf16: byUtf16, codePoints: byCodePoints, graphemes: byGraphemes, utf8Bytes: byUtf8Bytes, naiveUtf8Bytes };

// Ellipsis-aware display truncation: count in graphemes, reserve one for the ellipsis.
export function forDisplay(s, maxGraphemes, ellipsis = '…') {
  const g = graphemes(s);
  if (g.length <= maxGraphemes) return s;
  return g.slice(0, Math.max(0, maxGraphemes - 1)).join('') + ellipsis;
}

export function report(s, unit, limit) {
  const out = UNITS[unit](s, limit);
  const whole = graphemes(s);
  const kept = graphemes(out);
  const lastOk = kept.length === 0 || whole[kept.length - 1] === kept[kept.length - 1];
  return { unit, limit, out, ...measure(out), loneSurrogate: hasLoneSurrogate(out), replacementChar: out.includes('\uFFFD'), brokenLastCluster: !lastOk };
}

export const SAMPLES = {
  family: 'Order for \u{1F468}\u200D\u{1F469}\u200D\u{1F467} Geetha',
  flag: 'Ships to \u{1F1EE}\u{1F1F3} India',
  accent: 'Jose\u0301 returned it',
  emoji: 'Great book \u{1F600}\u{1F600} thanks',
};

if (process.argv[1]?.endsWith('truncate.mjs')) {
  console.log('node', process.version);
  for (const [name, s] of Object.entries(SAMPLES)) console.log(name, JSON.stringify(s), measure(s));
  const s = SAMPLES.family;
  for (const unit of Object.keys(UNITS)) for (const limit of [11, 13, 15]) {
    const r = report(s, unit, limit);
    console.log(unit.padEnd(15), String(limit).padStart(2), JSON.stringify(r.out).padEnd(28), `lone=${r.loneSurrogate} fffd=${r.replacementChar} brokenCluster=${r.brokenLastCluster}`);
  }
  console.log('display:', forDisplay(SAMPLES.accent, 6), '|', forDisplay(SAMPLES.flag, 11));
}

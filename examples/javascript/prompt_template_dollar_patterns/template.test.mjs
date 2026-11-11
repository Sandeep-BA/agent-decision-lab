// Author: Sandeep Belgavi.
import test from 'node:test';
import assert from 'node:assert/strict';
import { TEMPLATE, chainedReplace, chainedFunction, render } from './template.mjs';

const lang = 'English';
const cases = [
  ["refund $' please", 'Summarize the case below for the help desk.\nrefund \nReply in English. please\nReply in {{lang}}.'],
  ['Price was $$20', 'Summarize the case below for the help desk.\nPrice was $20\nReply in English.'],
  ['Quote $& end', 'Summarize the case below for the help desk.\nQuote {{case}} end\nReply in English.'],
  ['Before $` after', 'Summarize the case below for the help desk.\nBefore Summarize the case below for the help desk.\n after\nReply in English.'],
  ['See {{lang}} note', 'Summarize the case below for the help desk.\nSee English note\nReply in {{lang}}.'],
];

for (const [text, corrupted] of cases) {
  test(`chained string replace corrupts: ${JSON.stringify(text)}`, () => {
    assert.equal(chainedReplace(TEMPLATE, { case: text, lang }), corrupted);
  });
  test(`single pass keeps it literal: ${JSON.stringify(text)}`, () => {
    assert.equal(render(TEMPLATE, { case: text, lang }), `Summarize the case below for the help desk.\n${text}\nReply in English.`);
  });
}

test('function replacement fixes dollar patterns but not rescanning', () => {
  assert.equal(chainedFunction(TEMPLATE, { case: 'Price was $$20', lang }), 'Summarize the case below for the help desk.\nPrice was $$20\nReply in English.');
  assert.equal(chainedFunction(TEMPLATE, { case: 'See {{lang}} note', lang }).endsWith('Reply in {{lang}}.'), true);
});

test('$1 is literal for a string pattern', () => {
  assert.equal(chainedReplace(TEMPLATE, { case: 'Group $1', lang }), render(TEMPLATE, { case: 'Group $1', lang }));
});

test('missing value is an error, not a blank', () => {
  assert.throws(() => render(TEMPLATE, { case: 'x' }), /no value for \{\{lang\}\}/);
});

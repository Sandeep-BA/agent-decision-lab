// Author: Sandeep Belgavi.
import test from 'node:test';
import assert from 'node:assert/strict';
import { checkRedirect, naiveContains, naivePrefix } from './redirect.mjs';

const BAD = [
  ['//evil.example/login', 'host evil.example not allowed'],
  ['/\\evil.example', 'host evil.example not allowed'],
  ['/\t/evil.example', 'host evil.example not allowed'],
  ['https://books.example@evil.example/', 'userinfo not allowed'],
  ['https://books.example.evil.example/', 'host books.example.evil.example not allowed'],
  ['https://evil.example/?next=books.example', 'host evil.example not allowed'],
  ['javascript:alert(1)', 'scheme javascript: not allowed'],
  ['http://books.example/account', 'scheme http: not allowed'],
  ['https://books.example:8443/', 'explicit port 8443 not allowed'],
];

test('relative and allowlisted absolute targets pass and are normalized', () => {
  assert.deepEqual(checkRedirect('/account/orders?id=ORD-401'), { ok: true, target: 'https://books.example/account/orders?id=ORD-401' });
  assert.deepEqual(checkRedirect('HTTPS://HELP.Books.Example/cases/CASE-4402'), { ok: true, target: 'https://help.books.example/cases/CASE-4402' });
  assert.equal(checkRedirect('https://books.example:443/').ok, true); // default port is removed by the parser
});

for (const [input, reason] of BAD) {
  test(`rejects ${JSON.stringify(input)}`, () => {
    const result = checkRedirect(input);
    assert.equal(result.ok, false);
    assert.equal(result.reason, reason);
  });
}

test('the shortcuts accept targets the parser places on another host', () => {
  assert.equal(naivePrefix('//evil.example/login'), true);
  assert.equal(naivePrefix('https://books.example.evil.example/'), true);
  assert.equal(naivePrefix('https://books.example@evil.example/'), true);
  assert.equal(naiveContains('https://evil.example/?next=books.example'), true);
});

test('garbage and oversized values are rejected', () => {
  assert.equal(checkRedirect('').ok, false);
  assert.equal(checkRedirect('https://').ok, false);
  assert.equal(checkRedirect('/' + 'a'.repeat(3000)).ok, false);
});

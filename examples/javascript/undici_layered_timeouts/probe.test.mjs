// Author: Sandeep Belgavi. node --test probe.test.mjs  (about 10 s of loopback waits)
import test from 'node:test';
import assert from 'node:assert/strict';
import { CASES, attempt, startServer } from './probe.mjs';

const expected = ['complete', 'UND_ERR_BODY_TIMEOUT', 'UND_ERR_BODY_TIMEOUT', 'complete', 'UND_ERR_HEADERS_TIMEOUT', 'TimeoutError (deadline)'];

test('each timeout layer fails the way its documentation says', async () => {
  const server = await startServer();
  const { port } = server.address();
  try {
    for (const [i, [name, opts]] of CASES.entries()) {
      const r = await attempt(port, opts);
      assert.equal(r.outcome === 'complete' ? 'complete' : r.error, expected[i], name);
    }
  } finally {
    server.close();
  }
});

test('a body timeout is about silence, not total duration', async () => {
  const server = await startServer();
  const { port } = server.address();
  try {
    // About 1.5 s in total, but the longest silence in the body is 300 ms, under a 1 s bodyTimeout.
    const r = await attempt(port, { head: 1200, silence: 300, headersTimeout: 3000, bodyTimeout: 1000 });
    assert.equal(r.outcome, 'complete');
    assert.ok(r.ms >= 1400, `took ${r.ms} ms`);
  } finally {
    server.close();
  }
});

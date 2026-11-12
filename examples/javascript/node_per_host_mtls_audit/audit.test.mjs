// Author: Sandeep Belgavi. node --test for audit.mjs.
import test from 'node:test';
import assert from 'node:assert/strict';
import { versionStatus, agentKeyCollision, auditServer } from './audit.mjs';

test('version thresholds per line', () => {
  assert.equal(versionStatus('v22.23.4').status, 'vulnerable');
  assert.equal(versionStatus('v22.23.5').status, 'patched');
  assert.equal(versionStatus('v24.22.3').status, 'patched');
  assert.equal(versionStatus('v24.9.0').status, 'vulnerable');
  assert.equal(versionStatus('v26.13.0').status, 'vulnerable');
  assert.equal(versionStatus('v26.14.0').status, 'patched');
  assert.equal(versionStatus('v20.19.0').status, 'unsupported-line');
});

test('agent key collision matches the running binary', () => {
  const r = agentKeyCollision();
  const s = versionStatus();
  if (s.status === 'vulnerable') assert.equal(r.collides, true, 'unpatched binaries share one key for omitted ca and ca: []');
  assert.equal(typeof r.omitted, 'string');
});

test('CA-only SNI context is flagged', () => {
  const f = auditServer({ default: { cert: 'c', key: 'k', ca: 'customers', requestCert: true }, contexts: [{ host: 'admin.example.test', ca: 'staff' }], sessionIdContext: 'store' });
  assert.deepEqual(f.map(x => x.id), ['CVE-2026-123867', 'CVE-2026-123872']);
});

test('per-host client CAs on one listener are flagged', () => {
  const f = auditServer({ default: { cert: 'c', key: 'k', ca: 'customers', requestCert: true }, contexts: [{ host: 'admin.example.test', cert: 'a', key: 'b', ca: 'staff' }] });
  assert.deepEqual(f.map(x => x.id), ['CVE-2026-123872', 'CVE-2026-123872']);
});

test('a single policy server with sessionIdContext is clean', () => {
  assert.deepEqual(auditServer({ default: { cert: 'c', key: 'k', ca: 'customers', requestCert: true }, contexts: [], sessionIdContext: 'store' }), []);
});

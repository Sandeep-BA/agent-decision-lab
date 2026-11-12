// Author: Sandeep Belgavi. Offline triage for the Node.js 11 November 2026 TLS fixes.
// Reads no network, starts no server. Checks the running version, the https.Agent key
// collision behind CVE-2026-123877, and a declarative TLS server description for the
// per-host mTLS patterns named in the advisory.
import https from 'node:https';

export const FIXED = { 22: [22, 23, 5], 24: [24, 22, 3], 26: [26, 13, 1] };

export function versionStatus(version = process.version) {
  const [maj, min, pat] = version.replace(/^v/, '').split('.').map(Number);
  const fixed = FIXED[maj];
  if (!fixed) return { version, status: 'unsupported-line', detail: 'Not an active line in the 11 November 2026 advisory; end-of-life lines are affected.' };
  const cmp = [maj, min, pat].map((v, i) => v - fixed[i]).find(d => d !== 0) ?? 0;
  return { version, status: cmp >= 0 ? 'patched' : 'vulnerable', fixedIn: 'v' + fixed.join('.') };
}

export function agentKeyCollision() {
  const agent = new https.Agent();
  const base = { host: 'orders.example.test', port: 443 };
  const omitted = agent.getName({ ...base });
  const emptyCa = agent.getName({ ...base, ca: [] });
  return { omitted, emptyCa, collides: omitted === emptyCa };
}

// server: { default: {cert, key, ca, requestCert, rejectUnauthorized}, contexts: [{host, cert, key, ca}],
//           sessionIdContext }
export function auditServer(server) {
  const findings = [];
  const d = server.default || {};
  const perHost = (server.contexts || []).filter(c => c.ca && c.ca !== d.ca);
  for (const c of server.contexts || []) {
    if (c.ca && !c.cert) findings.push({ id: 'CVE-2026-123867', host: c.host, detail: 'SNI context sets a client CA without a server certificate; before the fix the default client CA was used instead.' });
  }
  if (perHost.length && d.requestCert) {
    findings.push({ id: 'CVE-2026-123872', host: '*', detail: 'One listener applies different client-CA policies per server name. Before the fix, TLS 1.2 renegotiation or session resumption could carry a client authenticated for one name to another. Upgrade; separate listeners per policy remove the shared-session path.' });
  }
  if (d.requestCert && !server.sessionIdContext) findings.push({ id: 'CVE-2026-123872', host: '*', detail: 'mTLS server without sessionIdContext; the fix disables resumption in this case.' });
  return findings;
}

if (process.argv[1] && process.argv[1].endsWith('audit.mjs')) {
  console.log(JSON.stringify({ version: versionStatus(), agent: agentKeyCollision() }, null, 2));
  const sample = {
    default: { cert: 'store.crt', key: 'store.key', ca: 'customers-ca', requestCert: true, rejectUnauthorized: true },
    contexts: [{ host: 'admin.books.example.test', ca: 'staff-ca' }],
  };
  console.log(JSON.stringify(auditServer(sample), null, 2));
}

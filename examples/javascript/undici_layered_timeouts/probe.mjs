// Author: Sandeep Belgavi. Loopback measurement of three timeout layers in undici:
// headersTimeout (wait for the response head), bodyTimeout (longest silence
// between body chunks) and an overall request deadline (AbortSignal.timeout).
// Times are scaled down to hundreds of milliseconds; the relationships are what matter.
import http from 'node:http';
import { Agent, fetch } from 'undici';

// A synthetic model stream: send headers after `headDelay`, then one chunk,
// then `silence` ms with nothing (the model writing one large tool argument),
// then the last chunk.
export function startServer() {
  const server = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x');
    const headDelay = Number(u.searchParams.get('head') ?? 0);
    const silence = Number(u.searchParams.get('silence') ?? 0);
    setTimeout(() => {
      res.writeHead(200, { 'content-type': 'text/event-stream' });
      res.write('data: {"text":"Drafting the reply for CASE-9120"}\n\n');
      setTimeout(() => {
        res.end('data: {"tool":"write_file","done":true}\n\n');
      }, silence);
    }, headDelay);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

export async function attempt(port, { head = 0, silence = 0, headersTimeout, bodyTimeout, deadline }) {
  const dispatcher = new Agent({ headersTimeout, bodyTimeout });
  const t0 = performance.now();
  try {
    const res = await fetch(`http://127.0.0.1:${port}/stream?head=${head}&silence=${silence}`, {
      dispatcher, signal: deadline ? AbortSignal.timeout(deadline) : undefined,
    });
    const text = await res.text();
    return { outcome: 'complete', chunks: text.split('\n\n').filter(Boolean).length, ms: Math.round(performance.now() - t0) };
  } catch (e) {
    const cause = e.name === 'TimeoutError' ? 'TimeoutError (deadline)' : (e.cause?.code ?? e.code ?? e.name);
    return { outcome: 'error', error: cause, ms: Math.round(performance.now() - t0) };
  } finally {
    await dispatcher.close().catch(() => {});
  }
}

export const CASES = [
  ['silence shorter than bodyTimeout', { silence: 300, headersTimeout: 1000, bodyTimeout: 1000 }],
  ['silence longer than bodyTimeout', { silence: 1500, headersTimeout: 1000, bodyTimeout: 1000 }],
  ['raised headersTimeout only (the pre-fix shape)', { silence: 1500, headersTimeout: 3000, bodyTimeout: 1000, deadline: 3000 }],
  ['bodyTimeout raised to the deadline (the fix shape)', { silence: 1500, headersTimeout: 3000, bodyTimeout: 3000, deadline: 3000 }],
  ['slow first byte, headersTimeout', { head: 1500, headersTimeout: 1000, bodyTimeout: 3000 }],
  ['deadline shorter than both', { silence: 1500, headersTimeout: 3000, bodyTimeout: 3000, deadline: 800 }],
];

if (process.argv[1]?.endsWith('probe.mjs')) {
  const server = await startServer();
  const { port } = server.address();
  console.log('node', process.version, 'undici (npm)', (await import('undici/package.json', { with: { type: 'json' } })).default.version);
  for (const [name, opts] of CASES) console.log(name.padEnd(52), JSON.stringify(await attempt(port, opts)));
  server.close();
}

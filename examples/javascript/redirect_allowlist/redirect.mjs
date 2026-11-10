// Author: Sandeep Belgavi. Validate a post-login redirect target with the WHATWG URL parser,
// the same algorithm browsers use, and redirect to the serialized result rather than the input.
// Node.js built-in URL only; no dependencies, no network.

export const POLICY = Object.freeze({
  base: 'https://books.example/',
  hosts: ['books.example', 'help.books.example'],
  schemes: ['https:'],
});

export function checkRedirect(input, policy = POLICY) {
  if (typeof input !== 'string' || input.length === 0 || input.length > 2048) {
    return { ok: false, reason: 'missing or oversized value' };
  }
  let url;
  try {
    url = new URL(input, policy.base);
  } catch {
    return { ok: false, reason: 'not a URL' };
  }
  if (!policy.schemes.includes(url.protocol)) return { ok: false, reason: `scheme ${url.protocol} not allowed`, url: url.href };
  if (url.username || url.password) return { ok: false, reason: 'userinfo not allowed', url: url.href };
  if (url.port !== '') return { ok: false, reason: `explicit port ${url.port} not allowed`, url: url.href };
  if (!policy.hosts.includes(url.hostname)) return { ok: false, reason: `host ${url.hostname} not allowed`, url: url.href };
  return { ok: true, target: url.href };
}

// Two common shortcuts, kept only so the tests can show what they let through.
export function naivePrefix(input) {
  return input.startsWith('/') || input.startsWith('https://books.example');
}

export function naiveContains(input) {
  return input.startsWith('/') || input.includes('books.example');
}

// Author: Sandeep Belgavi. Node.js fetch (undici) against the same loopback probe; run local_probe.py serve <status> first via run_node_probe.py.
const [port] = process.argv.slice(2);
const res = await fetch(`http://127.0.0.1:${port}/token`, {
  method: 'POST',
  headers: { Authorization: 'Bearer at-SYNTHETIC-111', 'X-Api-Key': 'key-SYNTHETIC-222', 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'grant_type=refresh_token&refresh_token=rt-SYNTHETIC-333&client_secret=cs-SYNTHETIC-444',
});
console.log(res.status);

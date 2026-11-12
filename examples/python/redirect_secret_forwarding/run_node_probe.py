"""Author: Sandeep Belgavi. Drive node_fetch_probe.mjs against local_probe.py for each redirect status."""
import json, subprocess, sys
for st in (301, 302, 303, 307, 308):
    srv = subprocess.Popen([sys.executable, "local_probe.py", "serve", str(st)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    port = json.loads(srv.stdout.readline())["origin"]
    subprocess.run(["node", "node_fetch_probe.mjs", str(port)], check=True, capture_output=True)
    out, _ = srv.communicate("done\n", timeout=10)
    rec = json.loads(out.strip().splitlines()[-1])
    ver = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    print(json.dumps(dict(rec, status=st, client="node fetch " + ver)))

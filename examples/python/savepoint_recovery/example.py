# Author: Sandeep Belgavi. Offline state model, not a PostgreSQL implementation.
class Transaction:
    def __init__(self):self.durable={};self.working={};self.markers=[];self.aborted=False
    def usable(self):
        if self.aborted:raise RuntimeError("transaction requires rollback")
    def insert(self,key,value):
        self.usable()
        if key in self.working:self.aborted=True;raise ValueError("duplicate identifier")
        self.working[key]=value
    def save(self,name):self.usable();self.markers.append((name,dict(self.working)))
    def marker(self,name):
        for i in range(len(self.markers)-1,-1,-1):
            if self.markers[i][0]==name:return i
        raise ValueError("unknown savepoint")
    def rollback_to(self,name):
        i=self.marker(name);self.working=dict(self.markers[i][1]);self.markers=self.markers[:i+1];self.aborted=False
    def release(self,name):self.usable();self.markers=self.markers[:self.marker(name)]
    def rollback(self):self.working=dict(self.durable);self.markers=[];self.aborted=False
    def commit(self):self.usable();self.durable=dict(self.working);self.markers=[]


def run_demo(fixture):
    tx = Transaction()
    tx.insert(11, "accepted-a")
    tx.save("optional")
    try:
        tx.insert(11, "duplicate-a")
    except ValueError:
        tx.rollback_to("optional")
    tx.insert(12, "accepted-b")
    tx.release("optional")
    before = sorted(tx.working)
    tx.rollback()
    return {"before_outer_rollback":before,"durable_rows":len(tx.durable)}

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))

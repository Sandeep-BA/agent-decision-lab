"""Author: Sandeep Belgavi. Durable-envelope graph fixture, no external service."""
import json
def child(parent,mid,kind):
 return {'id':mid,'correlation':parent['correlation'],'causes':[parent['id']],'kind':kind}
def ancestry(store,mid):
 pending=[mid];seen=set();result=[]
 while pending:
  current=pending.pop()
  if current in seen:continue
  seen.add(current)
  if current not in store:raise ValueError('unknown ancestor: '+current)
  row=store[current];result.append(current);pending.extend(row['causes'])
 return sorted(result)
def validate_child(parent,row):
 return row['correlation']==parent['correlation'] and parent['id'] in row['causes'] and row['id']!=parent['id']
def fixture():
 a={'id':'M1','correlation':'C1','causes':[],'kind':'analyze'}
 b=child(a,'M2','tag_proposed');c=child(b,'M3','tag_recorded');d=child(c,'M4','analyze')
 return {m['id']:m for m in (a,b,c,d)}
def demo():return {'ancestors':ancestry(fixture(),'M4'),'logical_messages':4,'attempts_for_M2':['try1','try2']}
if __name__=='__main__':print(json.dumps(demo(),sort_keys=True))

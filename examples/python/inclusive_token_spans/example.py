"""Author: Sandeep Belgavi. Synthetic inclusive usage; no provider or billing call."""
import json
def normalize(a):
 total=a.get('total');read=a.get('cache_read');create=a.get('cache_create')
 if any(type(x)is not int or x<0 for x in (total,read,create) if x is not None):raise ValueError('nonnegative integers required')
 if total is None:return {'total':None,'uncached':None,'status':'missing_total'}
 if read is None or create is None:return {'total':total,'uncached':None,'status':'partial_breakdown'}
 if read+create>total:raise ValueError('components exceed total')
 return {'total':total,'uncached':total-read-create,'status':'complete'}
def aggregate(rows):
 seen=set();total=0;read=0
 for r in rows:
  if r['span_id'] in seen:continue
  seen.add(r['span_id'])
  if r['kind']!='model_request':continue
  normalized=normalize(r)
  if normalized['status']!='complete':continue
  total+=r['total'];read+=r['cache_read']
 return {'total':total,'cache_read':read,'cache_share':read/total if total else None}
def demo():return normalize({'total':1200,'cache_read':900,'cache_create':100})
if __name__=='__main__':print(json.dumps(demo(),sort_keys=True))

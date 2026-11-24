"""Author: Sandeep Belgavi. Discrete scheduler fixture, not the Agents SDK."""
import json
def simulate(reject_at=3,guard=True,blocking=False,cooperative=True):
 if reject_at<0:raise ValueError('nonnegative time required')
 queue=['A','B','C'];active=None;start=None;effects=[];admitted=[];trace=[]
 for now in range(16):
  rejected=now>=reject_at
  if blocking and reject_at<=now:trace.append([now,'input rejected before work']);break
  if blocking:continue
  if active is not None:
   if now==start+2 and (not rejected or not cooperative):effects.append(active);trace.append([now,'effect '+active])
   if now>=start+4 or (rejected and cooperative):trace.append([now,'end '+active]);active=None
  if active is None and queue and not (guard and rejected):
   active=queue.pop(0);start=now;admitted.append([active,now]);trace.append([now,'start '+active])
 return {'admitted':admitted,'effects':effects,'queued':queue,'trace':trace}
def demo():return {'unchecked':simulate(guard=False),'guarded':simulate()}
if __name__=='__main__':print(json.dumps(demo(),sort_keys=True))

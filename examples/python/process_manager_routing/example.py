"""Author: Sandeep Belgavi. Synthetic artifact workflow, no model or effects."""
from dataclasses import dataclass, replace
import json
@dataclass(frozen=True)
class State:
    phase: str='awaiting_assessment'
    revision: int=4
    digest: str='D1'
    request: str='A17'

def handle(s,m):
    if m['revision']!=s.revision:return s,[], 'stale_revision'
    if s.phase!='awaiting_assessment':return s,[], 'unexpected_state'
    if m['kind']=='timeout':return replace(s,phase='awaiting_review',revision=s.revision+1),['open_review'],'applied'
    if m['kind']!='assessment':return s,[],'unsupported_message'
    if m.get('digest')!=s.digest or m.get('request')!=s.request:return s,[],'wrong_input'
    verdict=m.get('classification')
    phase={'accept':'accepted','reject':'rejected'}.get(verdict,'awaiting_review')
    return replace(s,phase=phase,revision=s.revision+1),['record_'+phase], 'applied'

def demo():
    s=State();timeout={'kind':'timeout','revision':4}
    late={'kind':'assessment','revision':4,'digest':'D1','request':'A17','classification':'accept'}
    s,commands,_=handle(s,timeout);s,more,reason=handle(s,late)
    return {'phase':s.phase,'commands':commands+more,'late_reply':reason}
if __name__=='__main__':print(json.dumps(demo(),sort_keys=True))

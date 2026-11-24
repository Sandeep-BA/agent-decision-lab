"""Author: Sandeep Belgavi. Synthetic event-time partition calculation."""
from datetime import date,datetime,time,timedelta,timezone
from zoneinfo import ZoneInfo
import json
UTC=timezone.utc
def bounds(day_text,zone_name):
 day=date.fromisoformat(day_text);zone=ZoneInfo(zone_name)
 return tuple(datetime.combine(d,time.min,zone).astimezone(UTC) for d in (day,day+timedelta(days=1)))
def partitions(start,end):
 if start.tzinfo is None or end.tzinfo is None or end<=start:raise ValueError('ordered aware interval required')
 current=datetime.combine(start.astimezone(UTC).date(),time.min,UTC);out=[]
 while current<end:
  following=current+timedelta(days=1)
  if following>start:out.append(current.date().isoformat())
  current=following
 return out
def select(events,start,end):
 out=[]
 for event in events:
  instant=datetime.fromisoformat(event['at'])
  if instant.tzinfo is None:raise ValueError('offset required')
  if start<=instant<end:out.append(event['id'])
 return out
def demo():
 start,end=bounds('2026-11-24','Asia/Kolkata')
 return {'start':start.isoformat(),'end':end.isoformat(),'partitions':partitions(start,end)}
if __name__=='__main__':print(json.dumps(demo(),sort_keys=True))

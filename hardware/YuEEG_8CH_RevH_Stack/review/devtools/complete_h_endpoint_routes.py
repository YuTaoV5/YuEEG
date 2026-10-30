from pathlib import Path
import json,math
from h_local_router import load
R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');ns=load();p,b,route,loc=[ns[k] for k in ['p','b','route','loc']]
objects={q.m_Uuid.AsString():q for f in b.GetFootprints() for q in f.Pads()};objects.update({q.m_Uuid.AsString():q for q in b.GetTracks()})
report=json.loads((R/'review/drc_ground_fill.json').read_text(encoding='utf8'));results=[]
def points(q):return [loc(q.GetPosition())] if isinstance(q,(p.PAD,p.PCB_VIA)) else [loc(q.GetStart()),loc(q.GetEnd())]
for v in report['unconnected_items']:
 a,c=[objects[x['uuid']] for x in v['items']];assert a.GetNetname()==c.GetNetname();aa,cc=min(((aa,cc) for aa in points(a) for cc in points(c)),key=lambda z:math.dist(*z))
 sl=0 if isinstance(a,(p.PAD,p.PCB_VIA)) else ns['layers'].index(a.GetLayer());el=0 if isinstance(c,(p.PAD,p.PCB_VIA)) else ns['layers'].index(c.GetLayer())
 print('Connect',a.GetNetname(),aa,cc,flush=True)
 try:
  route(a.GetNet(),aa,cc,width=.15,sl=sl,el=el);p.SaveBoard(str(ns['path']),b);results.append({'net':a.GetNetname(),'result':'routed'})
 except RuntimeError as e:print(str(e),flush=True);results.append({'net':a.GetNetname(),'result':str(e)})
 (R/'review/endpoint_route_results.json').write_text(json.dumps(results,indent=2))

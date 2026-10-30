from pathlib import Path
import pcbnew as p,wx,json,heapq,math
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');b=p.LoadBoard(str(R/'YuEEG_H_DIGITAL.kicad_pcb'));b.BuildConnectivity();c=b.GetConnectivity();result=[]
def pt(q):return (p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y))
def key(q):return q.m_Uuid.AsString()
for f in b.GetFootprints():
 if f.GetReference() not in ['C301','C302','C303','C304','C406','C407','C701','C702','C703','C704','C1006','C1007','C1008','C1009','C1101','C1102','C1103']:continue
 for pad in f.Pads():
  if pad.GetNetname() not in ['GND','HOST_GND']:continue
  start=pt(pad);seen={};todo=[(0,key(pad),pad,start)];best=None
  while todo:
   dist,uid,q,last=heapq.heappop(todo)
   if uid in seen:continue
   seen[uid]=dist
   if q.Type()==p.PCB_VIA_T or q.Type()==p.PCB_PAD_T and q!=pad and q.GetAttribute()==p.PAD_ATTRIB_PTH:best=dist;break
   for n in list(c.GetConnectedTracks(q))+list(c.GetConnectedPads(q)):
    if key(n) in seen:continue
    pts=[pt(n)] if n.Type() in [p.PCB_PAD_T,p.PCB_VIA_T] else [(p.ToMM(n.GetStart().x),p.ToMM(n.GetStart().y)),(p.ToMM(n.GetEnd().x),p.ToMM(n.GetEnd().y))]
    a=min(pts,key=lambda x:math.dist(last,x));end=pts[-1] if a==pts[0] else pts[0]
    heapq.heappush(todo,(dist+math.dist(last,a)+math.dist(a,end),key(n),n,end))
  result.append({'reference':f.GetReference(),'net':pad.GetNetname(),'ground_pad_xy_mm':start,'routed_distance_to_through_connection_mm':best})
(R/'review/decoupler_ground_paths.json').write_text(json.dumps(result,indent=2));print(*result,sep='\n')

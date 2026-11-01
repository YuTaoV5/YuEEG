from pathlib import Path
import pcbnew as p,wx,json,heapq,math,hashlib
wx.DisableAsserts();D=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=D/'YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));b.BuildConnectivity();c=b.GetConnectivity();objects={q.m_Uuid.AsString():q for q in b.GetTracks()}
for f in b.GetFootprints():objects.update({q.m_Uuid.AsString():q for q in f.Pads()})
def pt(q):return (p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y))
ground_planes={ly:[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(ly)] for ly in [p.In1_Cu,p.In3_Cu]}
def meets_ground_fill(v):
 for ly,zs in ground_planes.items():
  if not v.IsOnLayer(ly):continue
  radius=p.ToMM(v.GetWidth(ly))/2+.05
  for angle in range(0,360,45):
   point=p.VECTOR2I(v.GetPosition().x+p.FromMM(radius*math.cos(math.radians(angle))),v.GetPosition().y+p.FromMM(radius*math.sin(math.radians(angle))))
   if any(z.GetFilledPolysList(ly).Contains(point) for z in zs):return True
 return False
rows=[]
for f in b.GetFootprints():
 if not f.GetReference().startswith(('C180','U180')):continue
 for pad in f.Pads():
  if pad.GetNetname()!='GND':continue
  start=pt(pad);todo=[(0,pad.m_Uuid.AsString(),start)];seen=set();found=None
  while todo:
   distance,uid,last=heapq.heappop(todo)
   if uid in seen:continue
   seen.add(uid);q=objects[uid]
   if q.Type()==p.PCB_VIA_T and meets_ground_fill(q):found=distance;break
   if distance>15:continue
   for x in list(c.GetConnectedTracks(q))+list(c.GetConnectedPads(q)):
    key=x.m_Uuid.AsString()
    if key in seen or key not in objects:continue
    v=objects[key]
    points=[pt(v)] if v.Type() in [p.PCB_PAD_T,p.PCB_VIA_T] else [(p.ToMM(v.GetStart().x),p.ToMM(v.GetStart().y)),(p.ToMM(v.GetEnd().x),p.ToMM(v.GetEnd().y))]
    a=min(points,key=lambda z:math.dist(last,z));end=points[-1] if a==points[0] else points[0]
    heapq.heappush(todo,(distance+math.dist(last,a)+math.dist(a,end),key,end))
  rows.append(dict(reference=f.GetReference(),pad=pad.GetNumber(),xy_mm=start,estimated_track_path_to_via_meeting_ground_fill_mm=found))
r=dict(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rows=rows,scope='Native track graph to a via whose annulus neighborhood meets In1/In3GND fill. A through via inside the no-pour body is not sufficient. Endpoint-based lengths screen geometry; plane-island connectivity, return current distribution, inductance and impedance are not proven. Zones are not traversed. None means no such via found within15mm traversal, not an isolation claim.')
(D/'review/imu_ground_fill_paths.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(*rows,sep='\n')

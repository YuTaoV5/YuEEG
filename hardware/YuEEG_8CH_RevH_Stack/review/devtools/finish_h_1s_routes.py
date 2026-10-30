from pathlib import Path
import json,subprocess,math,pcbnew as p,wx
from h_local_router import load
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/power');path=R/'YuEEG_H_POWER.kicad_pcb';out=[]
for passno in range(4):
 report=R/'review/drc_1s_routing.json'
 subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','--output',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
 d=json.loads(report.read_text());print('Pass',passno,'violations',len(d['violations']),'gaps',len(d['unconnected_items']),flush=True)
 if not d['unconnected_items']:break
 ns=load('power');b,route,loc=[ns[k] for k in ['b','route','loc']]
 objects={q.m_Uuid.AsString():q for f in b.GetFootprints() for q in f.Pads()};objects.update({q.m_Uuid.AsString():q for q in b.GetTracks()})
 def points(q):return [loc(q.GetPosition())] if isinstance(q,(p.PAD,p.PCB_VIA)) else [loc(q.GetStart()),loc(q.GetEnd())]
 count=0
 for v in d['unconnected_items']:
  a,c=[objects[x['uuid']] for x in v['items']];assert a.GetNetname()==c.GetNetname();aa,cc=min(((aa,cc) for aa in points(a) for cc in points(c)),key=lambda z:math.dist(*z))
  sl=0 if isinstance(a,p.PCB_VIA) else ns['layers'].index(a.GetLayer());el=0 if isinstance(c,p.PCB_VIA) else ns['layers'].index(c.GetLayer())
  w=.3 if a.GetNetname() in ['GND','PACK_POS','PACK_FUSED','PACK_RP','BAT_PROTECTED_SENSE','SYS_5V','P_SW'] else .15
  print(a.GetNetname(),aa,cc,flush=True)
  try:route(a.GetNet(),aa,cc,width=w,sl=sl,el=el);p.SaveBoard(str(path),b);count+=1;out.append({'net':a.GetNetname(),'status':'routed','width_mm':w})
  except RuntimeError as e:print(e,flush=True);out.append({'net':a.GetNetname(),'status':str(e)})
 (R/'review/1s_route_results.json').write_text(json.dumps(out,indent=2))
 if not count:break

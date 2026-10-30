"""Straight bend trunks, no bend vias; route only in stiffened end regions."""
from pathlib import Path
import json,math,subprocess,hashlib
from h_local_router import load
D=Path('hardware/YuEEG_8CH_RevH_Stack/display_link');path=D/'YuEEG_H_DISPLAY_LINK.kicad_pcb';q=json.loads((D/'review/design_contract.json').read_text());project=path.with_suffix('.kicad_pro');project_bytes=project.read_bytes();ns=load('power',str(path),outline=q['outline_mm'],edge=.3,via=(.3,.1));p,b,route,pad,loc=[ns[k] for k in ['p','b','route','pad','loc']];a,c=q['bend_interval_flat_y_mm'];left=a;right=c
high=['AM_RST_P','AM_CS_P','AM_CLK_P','AM_D0_P','AM_D1_P','AM_D2_P','AM_D3_P'];low=['GND','AM_RAW','AM_1V8','TP_SDA_IDLE','TP_SCL_IDLE','VCI_EN'];lanes={};out=[]
def save():p.SaveBoard(str(path),b);project.write_bytes(project_bytes)
assert not list(b.GetTracks()),'Run only on fresh unrouted display-link layout'
for layer,names,xs in [(p.F_Cu,high,[6.35,5.15,4.75,3.95,4.35,5.95,5.55]),(p.B_Cu,low,[2.05,2.35,2.75,4.35,4.75,6.35])]:
 for net,x in zip(names,xs):
  x+=q['outline_mm'][0]/2-4.15
  actual_layer=p.F_Cu if net=='AM_RAW' else layer
  width=.30 if net=='GND' else .4 if net=='AM_RAW' else .15 if net=='AM_1V8' else .1;t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(x),p.FromMM(left)));t.SetEnd(p.VECTOR2I(p.FromMM(x),p.FromMM(right)));t.SetWidth(p.FromMM(width));t.SetLayer(actual_layer);t.SetNet(b.FindNet(net));b.Add(t);lanes[net]=(actual_layer,x)
for x in [3.45,5.55]:
 x+=q['outline_mm'][0]/2-4.15
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(x),p.FromMM(left)));t.SetEnd(p.VECTOR2I(p.FromMM(x),p.FromMM(right)));t.SetWidth(p.FromMM(.3));t.SetLayer(p.B_Cu);t.SetNet(b.FindNet('GND'));b.Add(t)
save()
for net in high+['VCI_EN','TP_SDA_IDLE','TP_SCL_IDLE','AM_1V8','AM_RAW','GND']:
 layer,x=lanes[net];li=ns['layers'].index(layer)
 for ref,y in [('JF1',left),('JF2',right)]:
  ns['route_clip_box']=(0,0,q['outline_mm'][0],left+1e-6) if ref=='JF1' else (0,right-1e-6,*q['outline_mm'])
  pads=[v for f in b.GetFootprints() if f.GetReference()==ref for v in f.Pads() if v.GetNetname()==net];pads.sort(key=lambda t:math.dist(loc(t.GetPosition()),(x,y)))
  for index,v in enumerate(pads):
   start=loc(v.GetPosition());targets=[(x,y,li)]
   if index:
    for t in b.GetTracks():
     if t.GetNetname()!=net:continue
     if isinstance(t,p.PCB_VIA):targets.append((*loc(t.GetPosition()),1))
     else:
      ly=ns['layers'].index(t.GetLayer());targets.extend([(*loc(t.GetStart()),ly),(*loc(t.GetEnd()),ly)])
   targets=[t for t in targets if (ref=='JF1' and t[1]<=left+1e-6) or (ref=='JF2' and t[1]>=right-1e-6)]
   tx,ty,el=min(targets,key=lambda t:math.dist(start,t[:2]));print(net,ref,v.GetNumber(),flush=True)
   try:
    route(v.GetNet(),start,(tx,ty),width=.15 if net in ['AM_RAW','GND','AM_1V8'] else .1,sl=1,el=el);save();out.append({'pin':ref+'.'+v.GetNumber(),'net':net,'status':'routed'})
   except RuntimeError as e:out.append({'pin':ref+'.'+v.GetNumber(),'net':net,'status':str(e)});print(e,flush=True)
   (D/'review/route_progress.json').write_text(json.dumps(out,indent=2))
report=D/'review/drc_current.json';subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','-o',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);d=json.loads(report.read_text(encoding='utf8'));print('Display link DRC',len(d['violations']),'unconnected',len(d['unconnected_items']),'parity',len(d['schematic_parity']));print([(v['type'],v['description']) for v in d['violations']][:8])


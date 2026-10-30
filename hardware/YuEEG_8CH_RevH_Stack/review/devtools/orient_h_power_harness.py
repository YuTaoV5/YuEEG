from pathlib import Path
import pcbnew as p,wx,json,sys,shutil
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';shutil.copy2(path,R/'review/before_harness_orientation.kicad_pcb');b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='JH2');assert f.GetOrientationDegrees()==0;f.SetOrientationDegrees(180)
new=[]
for pad in f.Pads():
 if not pad.GetNumber().isdigit():continue
 a=pad.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y);v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(35.85)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(pad.GetNet());new.append(v)
 t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(v.GetPosition());t.SetWidth(p.FromMM(.5));t.SetLayer(p.F_Cu);t.SetNet(pad.GetNet());new.append(t)
layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu];ripped={}
for q in list(f.Pads())+new:
 for layer in layers:
  if not q.IsOnLayer(layer):continue
  shape=q.GetEffectiveShape(layer)
  for ff in b.GetFootprints():
   if ff.GetReference()=='JH2':continue
   for a in ff.Pads():
    if a.IsOnLayer(layer) and a.GetNetCode()!=q.GetNetCode():assert not a.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)),(ff.GetReference(),a.GetNumber())
  for t in b.GetTracks():
   if t.GetNetCode()!=q.GetNetCode() and t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):ripped[t.m_Uuid.AsString()]=t.GetNetname()
for q in new:b.Add(q)
p.SaveBoard(str(path),b);sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
d=loads(path.read_text());d[:]=[q for q in d if not(isinstance(q,list) and q[0] in ['segment','via','arc'] and sub(q,'uuid') and json.loads(sub(q,'uuid')[1]) in ripped)];path.write_text(dumps(d));(R/'review/harness_orientation.json').write_text(json.dumps({'reference':'JH2','orientation_deg':180,'mating_direction':'toward -Y / device region; not into USB isolation corridor','position_mm':[34,35.3],'pins':{'1':'VBAT_SW','2':'VBAT_SW','3':'GND','4':'GND'},'ripped_items':ripped,'mechanical_requirement':'Retain harness entirely in device-side cable channel; confirm mated housing and FPC interference from samples/CAD'},indent=2));print('Power port faces device region; affected',len(ripped),'route items')
s=Path('logs/route_h_digital.py').read_text().replace("=='In1.Cu'","in ['In1.Cu','In3.Cu']");exec(s)

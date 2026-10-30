from pathlib import Path
import pcbnew as p,wx,json,shutil,sys
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';shutil.copy2(path,R/'review/before_buck_input_cap.kicad_pcb');b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()};f=fs['C406'];assert f.GetLayer()==p.F_Cu
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
f.Flip(f.GetPosition(),False);f.SetOrientationDegrees(0);f.SetPosition(xy(26.15,25.8));f.Reference().SetLayer(p.B_Fab);f.Value().SetLayer(p.B_Fab)
nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()};new=[]
def line(net,a,c,layer,width=.5):
 t=p.PCB_TRACK(b);t.SetStart(xy(*a));t.SetEnd(xy(*c));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);new.append(t)
def via(net,x,y):
 v=p.PCB_VIA(b);v.SetPosition(xy(x,y));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(nets[net]);new.append(v)
for net,x in [('VBAT_SW',24.675),('GND',27.625)]:
 via(net,x,27.25);line(net,(x,25.8),(x,27.25),p.B_Cu)
line('VBAT_SW',(24.675,27.25),(24.675,25.4875),p.F_Cu)
line('VBAT_SW',(24.675,25.4875),(25.325,25.4875),p.F_Cu,.3)
layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu];ripped={};issues=[]
for i,q in enumerate(new+list(f.Pads())):
 for layer in layers:
  if not q.IsOnLayer(layer):continue
  shape=q.GetEffectiveShape(layer)
  for ff in b.GetFootprints():
   for a in ff.Pads():
    if a.GetNetCode()!=q.GetNetCode() and a.IsOnLayer(layer) and a.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):issues.append([i,q.GetNetname(),ff.GetReference(),a.GetNumber()])
  for t in b.GetTracks():
   if t.GetNetCode()!=q.GetNetCode() and t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):ripped[t.m_Uuid.AsString()]=t.GetNetname()
assert not issues,issues
for q in new:b.Add(q)
p.SaveBoard(str(path),b)
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
d=loads(path.read_text());d[:]=[q for q in d if not(isinstance(q,list) and q[0] in ['segment','via','arc'] and sub(q,'uuid') and json.loads(sub(q,'uuid')[1]) in ripped)];path.write_text(dumps(d))
(R/'review/buck_input_cap.json').write_text(json.dumps({'reference':'C406','side':'B','center_mm':[26.15,25.8],'pad1_mm':[24.675,25.8],'pad2_mm':[27.625,25.8],'input_to_pin3_trace_mm':3.2125,'power_via_diameter_mm':.45,'power_via_drill_mm':.2,'ripped_items':ripped,'note':'Local input capacitor behind regulator; B-side assembly added to shorten input current loop. Ground returns through In1/In3 planes. Check actual capacitance under DC bias and assembly clearances.'},indent=2));print('Buck input capacitor relocated; ripped items',ripped)

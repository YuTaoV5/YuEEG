from pathlib import Path
import pcbnew as p,wx,json,sys,math
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));refs=['SW301','SW302','SW1001'];ys=[7.5,13.5,38];new=[];remove={}
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def loc(v):return p.ToMM(v.x),p.ToMM(v.y)
# Remove only the three old, deliberately placed left-hand central-pin escape pairs.
for t in b.GetTracks():
 if t.GetNetname()!='GND':continue
 if t.Type()==p.PCB_VIA_T:
  x,y=loc(t.GetPosition())
  if abs(x-.55)<.001 and any(abs(y-k)<.001 for k in ys):remove[t.m_Uuid.AsString()]='old central via'
 elif t.GetLayer()==p.F_Cu:
  a,c=loc(t.GetStart()),loc(t.GetEnd())
  if any(math.dist(a,(1.85,y))<.001 and math.dist(c,(.55,y))<.001 or math.dist(c,(1.85,y))<.001 and math.dist(a,(.55,y))<.001 for y in ys):remove[t.m_Uuid.AsString()]='old central track'
for ref in refs:
 f=next(f for f in b.GetFootprints() if f.GetReference()==ref);f.SetOrientationDegrees(270)
 for pad in f.Pads():
  if pad.GetNumber()!='2':continue
  x,y=loc(pad.GetPosition());vx=4.95 if abs(y-loc(f.GetPosition())[1])<.01 else .8
  v=p.PCB_VIA(b);v.SetPosition(xy(vx,y));v.SetWidth(p.FromMM(.4));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(pad.GetNet());new.append(v)
  t=p.PCB_TRACK(b);t.SetStart(pad.GetPosition());t.SetEnd(v.GetPosition());t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu);t.SetNet(pad.GetNet());new.append(t)
layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]
objects=new+[q for f in b.GetFootprints() if f.GetReference() in refs for q in f.Pads()]
for q in objects:
 for layer in layers:
  if not q.IsOnLayer(layer):continue
  shape=q.GetEffectiveShape(layer)
  for f in b.GetFootprints():
   for a in f.Pads():
    if a.GetNetCode()!=q.GetNetCode() and a.IsOnLayer(layer):assert not a.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)),(f.GetReference(),a.GetNumber(),q.GetNetname())
  for t in b.GetTracks():
   if t.GetNetCode()!=q.GetNetCode() and t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):remove[t.m_Uuid.AsString()]=t.GetNetname()
for q in new:b.Add(q)
p.SaveBoard(str(path),b);sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
d=loads(path.read_text());d[:]=[z for z in d if not(isinstance(z,list) and z[0] in ['segment','via','arc'] and sub(z,'uuid') and json.loads(sub(z,'uuid')[1]) in remove)];path.write_text(dumps(d));(R/'review/side_key_orientation.json').write_text(json.dumps({'references':refs,'orientation_deg':270,'center_x_mm':2.75,'actuator_tip_x_mm':.71,'actuator_direction':'-X / left edge','mechanical_basis':'Factory drawing + standard footprint F.Fab: body y=-1.35..1.21; actuator y=1.21..2.04. +Y local rotates to -X at 270 degrees.','source':'https://tech.alpsalpine.com/cms.media/product_detail_fig_skrt_d_21_en_3c9d642f3b.gif','ground_escapes':'central pad via to right x4.95; two grounded support tabs to left x0.8; all outside pads and underbody no-copper region','ripped_or_replaced_items':remove},indent=2));print('Side keys now face left board edge; updated',len(remove),'route items')
s=Path('logs/route_h_digital.py').read_text().replace("=='In1.Cu'","in ['In1.Cu','In3.Cu']");exec(s)

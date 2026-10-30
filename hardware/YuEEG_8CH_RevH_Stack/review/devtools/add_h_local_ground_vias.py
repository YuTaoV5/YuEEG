from pathlib import Path
import pcbnew as p,wx,math,json,shutil
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';shutil.copy2(path,R/'review/before_local_ground_vias.kicad_pcb');b=p.LoadBoard(str(path));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu];report=[]
def xy(a):return p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]))
def loc(v):return p.ToMM(v.x),p.ToMM(v.y)
def clear(item,skip_same=True,pads_all=False):
 for layer in layers:
  if not item.IsOnLayer(layer):continue
  shape=item.GetEffectiveShape(layer)
  for f in b.GetFootprints():
   for q in f.Pads():
    if q.IsOnLayer(layer) and (pads_all or q.GetNetCode()!=item.GetNetCode()) and q.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):return False
  for q in b.GetTracks():
   if q.IsOnLayer(layer) and (not skip_same or q.GetNetCode()!=item.GetNetCode()) and q.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):return False
  for z in b.Zones():
   if z.GetIsRuleArea() and z.IsOnLayer(layer) and z.GetDoNotAllowVias() and z.Outline().Collide(shape):return False
 if item.Type()==p.PCB_VIA_T:
  a=loc(item.GetPosition())
  for q in b.GetTracks():
   if q.Type()==p.PCB_VIA_T and math.dist(a,loc(q.GetPosition()))<.45:return False
 return True
refs=['C301','C302','C303','C304','C406','C407','C701','C702','C703','C704','C1006','C1007','C1008','C1009','C1101','C1102','C1103','U402','U701','U1001','U1003','U1004']
for ref in refs:
 f=next((f for f in b.GetFootprints() if f.GetReference()==ref),None)
 if f is None:continue
 for pad in f.Pads():
  if pad.GetNetname() not in ['GND','HOST_GND']:continue
  a=loc(pad.GetPosition());already=[q for q in b.GetTracks() if q.Type()==p.PCB_VIA_T and q.GetNetCode()==pad.GetNetCode() and math.dist(a,loc(q.GetPosition()))<.8]
  if already:report.append({'ref':ref,'pin':pad.GetNumber(),'status':'nearby_existing_via'});continue
  found=None
  for radius in [.55,.65,.75,.85,1,1.15,1.3,1.5,1.75,2]:
   for angle in range(0,360,15):
    c=(a[0]+radius*math.cos(math.radians(angle)),a[1]+radius*math.sin(math.radians(angle)))
    if not(.6<c[0]<47.4 and .6<c[1]<59.4):continue
    via=p.PCB_VIA(b);via.SetPosition(xy(c));via.SetWidth(p.FromMM(.4));via.SetDrill(p.FromMM(.2));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH);via.SetNet(pad.GetNet())
    if not clear(via,pads_all=True):continue
    t=p.PCB_TRACK(b);t.SetStart(pad.GetPosition());t.SetEnd(xy(c));t.SetWidth(p.FromMM(.2));t.SetLayer(f.GetLayer());t.SetNet(pad.GetNet())
    if not clear(t):continue
    b.Add(via);b.Add(t);found=c;break
   if found:break
  report.append({'ref':ref,'pin':pad.GetNumber(),'status':'added' if found else 'no_clear_site_within_2mm','via_xy_mm':found,'pad_to_via_mm':math.dist(a,found) if found else None})
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);(R/'review/local_ground_vias.json').write_text(json.dumps(report,indent=2));print(*report,sep='\n')

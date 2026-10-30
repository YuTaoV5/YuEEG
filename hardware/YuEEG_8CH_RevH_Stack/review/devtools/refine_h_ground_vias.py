from pathlib import Path
import json,math,shutil
src=Path('logs/add_h_local_ground_vias.py').read_text().split('refs=')[0]
src=src.replace("shutil.copy2(path,R/'review/before_local_ground_vias.kicad_pcb');",'')
src=src.replace('for q in b.GetTracks():\n   if q.IsOnLayer','for q in []:\n   if q.IsOnLayer')
ns={};exec(src,ns)
for k,v in ns.items():globals()[k]=v
shutil.copy2(path,R/'review/before_ground_refinement.kicad_pcb')
results=[]
for ref in ['C1008','C1007','C1006','C1101']:
 f=next(f for f in b.GetFootprints() if f.GetReference()==ref);pad=next(q for q in f.Pads() if q.GetNetname()=='GND');a=loc(pad.GetPosition());best=None
 for radius in [.65,.75,.85,1,1.15,1.3,1.5,1.75,2]:
  for angle in range(0,360,15):
   c=(a[0]+radius*math.cos(math.radians(angle)),a[1]+radius*math.sin(math.radians(angle)))
   v=p.PCB_VIA(b);v.SetPosition(xy(c));v.SetWidth(p.FromMM(.4));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(pad.GetNet())
   t=p.PCB_TRACK(b);t.SetStart(pad.GetPosition());t.SetEnd(xy(c));t.SetWidth(p.FromMM(.2));t.SetLayer(f.GetLayer());t.SetNet(pad.GetNet())
   if not clear(v,pads_all=True) or not clear(t):continue
   ripped={}
   for item in [v,t]:
    for layer in layers:
     if not item.IsOnLayer(layer):continue
     shape=item.GetEffectiveShape(layer)
     for q in b.GetTracks():
      if q.GetNetCode()!=item.GetNetCode() and q.IsOnLayer(layer) and q.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):ripped[q.m_Uuid.AsString()]=q
   if any(q.GetNetname().startswith(('USB_','MCU_')) or q.GetNetname()=='BUCK_SW' for q in ripped.values()):continue
   score=(len(ripped),radius)
   if best is None or score<best[0]:best=score,v,t,ripped,c
 if best is None or best[0][0]>3:results.append({'ref':ref,'result':'no acceptable local site'});continue
 score,v,t,ripped,c=best
 records=[{'uuid':key,'net':q.GetNetname()} for key,q in ripped.items()]
 # Remove by raw UUID after save in a fresh load to avoid SWIG iterator invalidation.
 b.Add(v);b.Add(t);results.append({'ref':ref,'via_xy_mm':c,'pad_to_via_mm':score[1],'ripped':records})
 # Native removal is safe here when no footprint/shape wrappers are removed.
 for q in ripped.values():b.Remove(q)
p.SaveBoard(str(path),b);(R/'review/ground_refinement.json').write_text(json.dumps(results,indent=2));print(*results,sep='\n')

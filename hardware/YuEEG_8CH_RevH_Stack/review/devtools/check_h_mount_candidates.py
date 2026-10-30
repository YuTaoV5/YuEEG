import pcbnew as p,wx,json
from pathlib import Path
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack');out=[]
for board in ['afe','digital']:
 b=p.LoadBoard(str(R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb')))
 for pos in [(44,4),(44,51),(4,55)]:
  v=p.VECTOR2I(*[p.FromMM(z) for z in pos]);hole=p.SHAPE_CIRCLE(v,p.FromMM(1.1));courts=p.SHAPE_CIRCLE(v,p.FromMM(2.25));hits=[];bodies=[]
  for f in b.GetFootprints():
   for q in f.Pads():
    for layer in b.GetEnabledLayers().CuStack():
     if q.IsOnLayer(layer) and q.GetEffectiveShape(layer).Collide(hole,p.FromMM(.25)):hits.append([f.GetReference()+'.'+q.GetNumber(),p.LayerName(layer)])
   for g in f.GraphicalItems():
    if g.GetLayer() in [p.F_CrtYd,p.B_CrtYd] and g.GetEffectiveShape().Collide(courts,0):bodies.append(f.GetReference())
  for t in b.GetTracks():
   for layer in b.GetEnabledLayers().CuStack():
    if t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(hole,p.FromMM(.25)):hits.append([t.m_Uuid.AsString(),t.GetNetname(),p.LayerName(layer)])
  out.append({'board':board,'xy_mm':pos,'copper_hits':hits,'courtyard_boundary_hits':sorted(set(bodies))})
print(json.dumps(out,indent=2));(R/'review/mounting_candidate_screen.json').write_text(json.dumps(out,indent=2))

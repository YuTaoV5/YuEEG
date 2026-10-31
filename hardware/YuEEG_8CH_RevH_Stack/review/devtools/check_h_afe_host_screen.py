"""Conditional C405/body and native all-layer copper screening; not isolation certification."""
from pathlib import Path
import json,hashlib,math,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');path=H/'afe/YuEEG_H_AFE.kicad_pcb';b=p.LoadBoard(str(path));ext=json.loads(Path('logs/host_external.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();cu=[]
def box(shape):
 r=shape.BBox();return [p.ToMM(v) for v in [r.GetX(),r.GetY(),r.GetRight(),r.GetBottom()]]
for f in b.GetFootprints():
 for pad in f.Pads():
  for ly in b.GetEnabledLayers().CuStack():
   if pad.IsOnLayer(ly):cu.append(dict(kind='pad',layer=b.GetLayerName(ly),ref=f.GetReference()+'.'+pad.GetNumber(),bbox=box(pad.GetEffectiveShape(ly))))
for t in b.GetTracks():
 for ly in b.GetEnabledLayers().CuStack():
  if t.IsOnLayer(ly):cu.append(dict(kind='track/via',layer=b.GetLayerName(ly),ref=t.m_Uuid.AsString(),bbox=box(t.GetEffectiveShape(ly))))
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for ly in b.GetEnabledLayers().CuStack():
  if z.IsOnLayer(ly) and z.HasFilledPolysForLayer(ly):cu.append(dict(kind='filled_zone',layer=b.GetLayerName(ly),ref=z.GetZoneName(),bbox=box(z.GetFilledPolysList(ly))))
maximum=max(cu,key=lambda v:v['bbox'][3]);assert maximum['bbox'][3]<=47.5001,maximum
f=next(f for f in b.GetFootprints() if f.GetReference()=='C405');x,y=[p.ToMM(v) for v in [f.GetPosition().x,f.GetPosition().y]];assert (x,y)==(3.9,42.5)
cap=[x-1.75-.4,y-.95-.4,0,x+1.75+.4,y+.95+.4,2.0];pairs=[]
for v in ext['external_items']:
 lo=v['bounds_mm'];z=8.2-.3 if v['layer']=='B.Cu' else 8.2+1.5;upper=[lo[0],lo[1],z,lo[2],lo[3],z+.3];distance=math.sqrt(sum(max(upper[i]-cap[i+3],cap[i]-upper[i+3],0)**2 for i in range(3)));pairs.append((distance,v))
minimum,item=min(pairs,key=lambda v:v[0]);assert minimum>8
result=dict(status='CONDITIONAL_C405_AND_COPPER_SCREEN_NOT_ASSEMBLY_RELEASE',afe_pcb_sha256=sha(path),digital_pcb_sha256=ext['pcb_sha256'],external_host_copper_extract=ext,afe_native_copper_item_count=len(cu),afe_copper_y_max_mm=maximum['bbox'][3],afe_y_max_primitive=maximum,all_layer_exclusion_start_y_mm=47.5,c405_mpn='MSASE31LBB7226MTNA01',c405_position_mm=[x,y],c405_max_body_mm=[3.5,1.9,1.9],cap_envelope_including_solder_and_xy_allowance_mm=cap,relative_xy_registration_allowance_mm=.4,minimum_local_surface_gap_required_mm=8.2,upper_host_back_solder_allowance_mm=.3,upper_board_min_thickness_assumed_mm=1.5,c405_minimum_external_host_lower_bound_mm=minimum,nearest_external_host_primitive=item,scope='Distances between conservative primitive bounding boxes. HOST In1/In3 planes are embedded and excluded from bare external-copper distances; PCB dielectric and full insulation system require separate qualification. Does not bound all components, wires, mounting hardware, battery or contamination. Assembly assumptions require verification.')
(H/'mechanical/current/afe_host_screen.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('AFE all-layer copper max Y',maximum['bbox'][3],'C405 conditional distance',minimum)

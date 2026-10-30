"""Conservative XY screening for the selected USB-on-digital architecture.

Battery case is treated as a full conductive envelope for screening only.
No statement about actual exposed conductors, creepage or certified isolation.
"""
from pathlib import Path
import pcbnew as p,json,math,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');out=H/'mechanical/current';boards={name:p.LoadBoard(str(H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb'))) for name in ['afe','digital','power']};b=boards['digital'];pro=json.loads((H/'digital/YuEEG_H_DIGITAL.kicad_pro').read_text());host={r['pattern'] for r in pro['net_settings']['netclass_patterns'] if r['netclass']=='USB_HOST'};bounds=[]
def rect(box):return [p.ToMM(v) for v in [box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]]
for f in b.GetFootprints():
 for q in f.Pads():
  if q.GetNetname() in host:
   for ly in b.GetEnabledLayers().CuStack():
    if q.IsOnLayer(ly):bounds.append(rect(q.GetEffectiveShape(ly).BBox()))
for t in b.GetTracks():
 if t.GetNetname() in host:
  for ly in b.GetEnabledLayers().CuStack():
   if t.IsOnLayer(ly):bounds.append(rect(t.GetEffectiveShape(ly).BBox()))
for z in b.Zones():
 if not z.GetIsRuleArea() and z.GetNetname() in host:bounds.append(rect(z.Outline().BBox()))
host_box=[min(r[0] for r in bounds),min(r[1] for r in bounds),max(r[2] for r in bounds),max(r[3] for r in bounds)]
f=next(f for f in boards['afe'].GetFootprints() if f.GetReference()=='J1301');qs=[rect(g.GetBoundingBox()) for g in f.GraphicalItems() if g.GetLayer()==p.F_CrtYd];header=[min(q[0] for q in qs),min(q[1] for q in qs),max(q[2] for q in qs),max(q[3] for q in qs)]
def separation(a,c):return math.hypot(max(a[0]-c[2],c[0]-a[2],0),max(a[1]-c[3],c[1]-a[3],0))
def overlaps(a,c):return min(a[2],c[2])>max(a[0],c[0]) and min(a[3],c[3])>max(a[1],c[1])
screen=json.loads((out/'screen_envelope_review.json').read_text());rows=[]
for label,side,gap,y in [('left_2mm','left',2,0),('right_2mm','right',2,0),('right_5mm','right',5,0),('right_6mm','right',6,0),('right_2mm_forward_3mm','right',2,-3)]:
 x=48+gap if side=='right' else -gap-29.9;box=[x,y,x+29.9,y+42.7];distance=separation(box,host_box)
 rows.append({'name':label,'battery_body_xy_mm':box,'board_edge_gap_mm':gap,'battery_y_offset_mm':y,'host_xy_envelope_separation_mm':distance,'meets_8mm_xy_screen':distance>=8,'overlaps_afe_electrode_header_courtyard_xy':overlaps(box,header)})
chosen=next(r for r in rows if r['name']=='right_6mm');report={'status':'CONDITIONAL_MECHANICAL_SCREENING_NOT_ASSEMBLY_RELEASE','selected_architecture':'USB isolation, Type-C and host protection stay on digital; stack may exceed screen','baseline_pcb_sha256':{name:hashlib.sha256((H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb')).read_bytes()).hexdigest() for name in boards},'battery_model':'Sony NP-BX1','battery_dimensions_whd_mm':[29.9,9.2,42.7],'battery_dimensions_source':'https://pro.sony/s3/cms-static-content/operation-manual/4447543111.pdf','dimensions_status':'Manufacturer approximate envelope, not a mechanical tolerance drawing','host_copper_xy_bounding_envelope_mm':host_box,'afe_electrode_header_courtyard_xy_mm':header,'screen_projection_xy_mm':screen['screen_projection_mm'],'candidate_layouts':rows,'proposed_layout':chosen['name'],'proposed_battery_body_z_mm':[0,9.2],'design_target_xy_mm':8,'scope':'XY lower-bound screening against a bounding rectangle enclosing native HOST-class pad/track copper and zone outlines. Z is deliberately ignored. Battery full case treated conservatively as a conductor envelope, not claimed to be exposed metal. No actual electrode collision, certified isolation or assembly claim. Host bodies, enclosure surfaces, cables, tolerances, RF antenna and screen FPC require separate review.'}
(out/'battery_side_envelope.json').write_text(json.dumps(report,indent=2));print('HOST XY',host_box,'electrode header courtyard',header);print([(r['name'],round(r['host_xy_envelope_separation_mm'],3),r['overlaps_afe_electrode_header_courtyard_xy']) for r in rows])

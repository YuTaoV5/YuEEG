"""Conservative XY screening of new digital PH4 solder tails over the AFE."""
from pathlib import Path
import pcbnew as p,wx,json,hashlib
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');dp=H/'digital/YuEEG_H_DIGITAL.kicad_pcb';ap=H/'afe/YuEEG_H_AFE.kicad_pcb';db=p.LoadBoard(str(dp));ab=p.LoadBoard(str(ap));f=next(f for f in db.GetFootprints() if f.GetReference()=='JH2');checks=[]
for pad in f.Pads():
 box=pad.GetBoundingBox();bb=[p.ToMM(box.GetX())-.25,p.ToMM(box.GetY())-.25,p.ToMM(box.GetRight())+.25,p.ToMM(box.GetBottom())+.25];hits=[];nearest=1e6;nearref=None
 for g in ab.GetFootprints():
  if g.GetLayer()!=p.F_Cu:continue
  pts=[v for q in g.GraphicalItems() if q.GetLayer()==p.F_CrtYd for v in [q.GetStart(),q.GetEnd()]]
  if not pts:continue
  other=[min(p.ToMM(v.x) for v in pts),min(p.ToMM(v.y) for v in pts),max(p.ToMM(v.x) for v in pts),max(p.ToMM(v.y) for v in pts)];dx=max(bb[0]-other[2],other[0]-bb[2],0);dy=max(bb[1]-other[3],other[1]-bb[3],0);dist=(dx*dx+dy*dy)**.5
  if dist<nearest:nearest=dist;nearref=g.GetReference()
  if dx==0 and dy==0:hits.append(dict(reference=g.GetReference(),value=g.GetValue(),courtyard_xy_mm=other))
 checks.append(dict(pin=pad.GetNumber(),reserved_tail_xy_mm=bb,overlapping_afe_courtyards=hits,nearest_courtyard=nearref,xy_distance_mm=nearest))
report=dict(status='CONDITIONAL_TAIL_SCREEN_NOT_ASSEMBLY_RELEASE',digital_pcb_sha256=hashlib.sha256(dp.read_bytes()).hexdigest(),afe_pcb_sha256=hashlib.sha256(ap.read_bytes()).hexdigest(),surface_gap_mm=8.5,maximum_tail_solder_projection_allowed_below_digital_mm=1.2,additional_reserved_xy_margin_around_pad_bbox_mm=.25,required_afe_component_height_max_for_0_5mm_vertical_margin_mm=6.8,intersecting_capacitor=dict(reference='C220',mpn='EEEFT1E101AP',catalog_length_nominal_mm=5.8,catalog_length_max_mm=6.1,source='https://industrial.panasonic.com/cdbs/www-data/pdf/RDE0000/ABA0000C1240.pdf',nominal_gap_minus_trimmed_tail_and_cap_max_mm=1.2,additional_assumed_cap_solder_lift_mm=.1,conditional_clearance_after_cap_solder_lift_mm=1.1),checks=checks,scope='Pad bounding boxes enlarged by .25mm screen entire tail/solder projection, which overestimates bare lead width. JH2 tails must be trimmed/inspected to at most 1.2mm including solder below digital B; not a guaranteed supplier maximum. Current XY overlaps C220. 8.5mm nominal gap minus 1.2mm tail, 6.1mm capacitor maximum and assumed .1mm solder lift leaves 1.1mm before board-gap/warpage tolerances. Does not qualify all interboard parts or the full assembly.')
(H/'mechanical/current/power_port_tail_review.json').write_text(json.dumps(report,indent=2));print([(c['pin'],[v['reference'] for v in c['overlapping_afe_courtyards']],c['xy_distance_mm']) for c in checks])

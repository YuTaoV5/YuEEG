"""Native current pogo bores against part and reference-fabricator tolerances."""
from pathlib import Path
import json,hashlib,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');M=H/'mechanical/current';pcb=H/'power/YuEEG_H_POWER.kicad_pcb';facts=M/'pogo_source_and_hole_review.json';adopt=M/'pogo_hole_tolerance_adoption.json';reference=M/'pogo_reference.json';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();d=json.loads(facts.read_text());a=json.loads(adopt.read_text());assert sha(pcb)==a['current_pcb_sha256']
part=d['resolved_dimensions'];tail_max=(part['tail_diameter_nominal_inch']+part['diameter_tolerance_inch'])*25.4;clearance=part['recommended_minimum_hole_diametral_clearance_inch']*25.4;minimum=tail_max+clearance;tol=d['fabricator_reference']['PTH_tolerance_mm'];assert abs(minimum-.5842)<1e-9
b=p.LoadBoard(str(pcb));f=next(f for f in b.GetFootprints() if f.GetReference()=='JP1');rows=[];hits=[]
for pad in f.Pads():
 assert pad.GetAttribute()==p.PAD_ATTRIB_PTH and pad.GetDrillSize().x==pad.GetDrillSize().y
 hole=p.ToMM(pad.GetDrillSize().x);size=min(p.ToMM(pad.GetSize().x),p.ToMM(pad.GetSize().y));assert hole==json.loads(reference.read_text())['project_finished_hole_mm']==.7
 low=hole-tol['minus'];high=hole+tol['plus'];assert low>minimum and (size-high)/2>.15
 circle=p.SHAPE_CIRCLE(pad.GetPosition(),pad.GetDrillSize().x//2)
 for other in b.GetFootprints():
  for q in other.Pads():
   if q.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(circle,q.GetEffectiveShape(q.GetLayer()),p.FromMM(.2499)):hits.append({'probe_pin':pad.GetNumber(),'pad':other.GetReference()+'.'+q.GetNumber()})
 rows.append({'pin':pad.GetNumber(),'net':pad.GetNetname(),'nominal_finished_hole_mm':hole,'reference_process_finished_bounds_mm':[round(low,4),round(high,4)],'diametral_clearance_at_max_tail_and_min_hole_mm':round(low-tail_max,4),'margin_over_part_recommendation_mm':round(low-minimum,4),'pad_minimum_copper_span_mm':size,'nominal_geometric_annular_ring_mm':round((size-hole)/2,4),'geometric_annular_ring_at_largest_reference_hole_mm':round((size-high)/2,4)})
assert len(rows)==2 and not hits
out={'status':'PASS_REFERENCE_PROCESS_GEOMETRY_NOT_SOLDER_HOLDER_QUALIFICATION','pcb_sha256':sha(pcb),'source_fact_sha256':sha(facts),'probe_reference_sha256':sha(reference),'footprint_library_sha256':sha(H/'footprints/YuEEG.pretty/NPBX1_MillMax0906_Dplus_Bminus_10mm.kicad_mod'),'adoption_sha256':sha(adopt),'required_worst_case_minimum_finished_hole_mm':round(minimum,4),'minimum_hole_to_other_SMD_copper_mm':.25,'rows':rows,'hits':hits,'scope':'Two native JP1 bores, fullSMD hole/copper check including same-net, plus stated part/fabricator diameter bounds. Ring result excludes hole-position/copper etch variation. No claim of actual accepted fab tolerance, pin-centering, solder fillet, contact alignment tolerance, retention or physical fit.'}
(M/'pogo_hole_fit_review.json').write_text(json.dumps(out,indent=2),encoding='utf8');print('PASS current JP1 holes:0.62mm min under reference process >0.5842mm recommendation; rings and SMT clearance screened')

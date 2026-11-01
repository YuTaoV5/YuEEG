from pathlib import Path
import pcbnew as p,wx,json,hashlib,csv
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'digital';a=p.LoadBoard(str(H/'afe/YuEEG_H_AFE.kicad_pcb'));b=p.LoadBoard(str(D/'YuEEG_H_DIGITAL.kicad_pcb'))
def box(f,layer):
 ss=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
 return [min(p.ToMM(s.GetX()) for s in ss),min(p.ToMM(s.GetY()) for s in ss),max(p.ToMM(s.GetX()+s.GetWidth()) for s in ss),max(p.ToMM(s.GetY()+s.GetHeight()) for s in ss)] if ss else None
afebom={r['Reference']:r for r in csv.DictReader((H/'afe/BOM.csv').open(encoding='utf-8-sig'))};rows=[];heights={'U1801':3.0,'U1802':1.45,'C1801':1.55,'C1802':1.8,'C1803':1.55,'C1804':.95,'C1805':.95,'C1806':1.45,'C1807':1.45}
for f in b.GetFootprints():
 ref=f.GetReference()
 if not ref.startswith(('U180','C180','R180')):continue
 bb=box(f,p.B_CrtYd)
 if ref=='U1801':cx,cy=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y);bb=[cx-7.35,cy-6.7,cx+7.35,cy+6.7]
 h=heights.get(ref,.45);hits=[]
 for q in a.GetFootprints():
  if q.GetLayer()!=p.F_Cu:continue
  qb=box(q,p.F_CrtYd)
  if qb and max(bb[0],qb[0])<min(bb[2],qb[2]) and max(bb[1],qb[1])<min(bb[3],qb[3]):hits.append(dict(reference=q.GetReference(),value=q.GetValue(),footprint=afebom[q.GetReference()]['Footprint'],courtyard_mm=qb))
 rows.append(dict(reference=ref,conservative_xy_mm=bb,maximum_component_height_mm=h,assumed_solder_lift_mm=.1,opposing_afe_height_budget_with_0p5mm_margin_at_required_8p3_gap_mm=round(8.3-h-.1-.5,2),opposing_afe=hits))
r=dict(status='CONDITIONAL_INTERBOARD_HEIGHT_BUDGET_NOT_ASSEMBLY_RELEASE',digital_pcb_sha256=hashlib.sha256((D/'YuEEG_H_DIGITAL.kicad_pcb').read_bytes()).hexdigest(),afe_pcb_sha256=hashlib.sha256((H/'afe/YuEEG_H_AFE.kicad_pcb').read_bytes()).hexdigest(),nominal_surface_gap_mm=8.5,required_minimum_local_gap_mm=8.3,rows=rows,scope='Require measured local surface gap at least8.3mm, mounted C220 at most6.2mm including solder, and LDO/C1806 at most1.55mm including solder; this leaves at least0.55mm nominal-envelope separation there. This is an assembly acceptance condition, not a verified tolerance. Conservative courtyard XY screening of all16 new backside parts. Sensor envelope intentionally exceeds nominal. Sensor/cap/LDO heights from selected-package documentation; resistor .45mm is an imposed procurement envelope. Opposing AFE heights must be bound to delivered parts, local gap/warpage and supports measured. No complete tolerance stack, CAD solid collision or physical validation claim.')
(H/'mechanical/current/imu_interboard_review.json').write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf8');print(*[(q['reference'],q['opposing_afe_height_budget_with_0p5mm_margin_at_required_8p3_gap_mm'],[v['reference'] for v in q['opposing_afe']]) for q in rows],sep='\n')

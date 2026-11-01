"""Check the actual SMT pair, logical contact mapping and drawing dimensions."""
from pathlib import Path
import pcbnew as p, wx, json, hashlib, math
wx.DisableAsserts()
R=Path('hardware/YuEEG_8CH_RevH_Stack');fs={};sources={};footprints={}
for name in ['afe','digital']:
 path=R/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='JH1');fs[name]=(b,f)
 assert f.GetAttributes() & p.FP_SMD and '5001-BTB08' in f.GetValue(), 'Pin headers are no longer an allowed interboard design'
 assert f.GetLayer()==(p.F_Cu if name=='afe' else p.B_Cu)
 assert math.dist([p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)],[43.7,21])<.00001
 pads=[q for q in f.Pads() if q.GetNumber()];locators=[q for q in f.Pads() if not q.GetNumber()]
 assert len(pads)==20 and len(locators)==2
 assert all(q.GetAttribute()==p.PAD_ATTRIB_SMD and not q.GetDrillSize().x for q in pads)
 assert all(q.GetAttribute()==p.PAD_ATTRIB_NPTH and abs(p.ToMM(q.GetDrillSize().x)-.65)<.00001 for q in locators)
 assert all(abs(p.ToMM(q.GetSize().x)-.35)<.00001 and abs(p.ToMM(q.GetSize().y)-1.8)<.00001 for q in pads)
 rules=list(f.Zones());assert len(rules)==1
 rule=rules[0];assert rule.GetIsRuleArea() and all([rule.GetDoNotAllowTracks(),rule.GetDoNotAllowVias(),rule.GetDoNotAllowPads(),rule.GetDoNotAllowCopperPour()])
 assert set(rule.GetLayerSet().Seq())=={p.F_Cu if name=='afe' else p.B_Cu}
 sources[name]=hashlib.sha256(path.read_bytes()).hexdigest()
 fpname='JME_BTB0845_20FR_Logical' if name=='afe' else 'JME_BTB0840_20MR_Logical'
 footprints[fpname+'.kicad_mod']=hashlib.sha256((R/'footprints/YuEEG.pretty'/(fpname+'.kicad_mod')).read_bytes()).hexdigest()
a={q.GetNumber():q for q in fs['afe'][1].Pads() if q.GetNumber()};out=[]
contract=json.loads((R/'review/interboard_contract.json').read_text(encoding='utf8'))['AFE_DIGITAL']
for q in fs['digital'][1].Pads():
 if not q.GetNumber():continue
 other=a[q.GetNumber()];assert q.GetNetname()==other.GetNetname()==contract[q.GetNumber()]
 assert (q.GetPosition()-other.GetPosition()).EuclideanNorm()<p.FromMM(.001)
 i=(int(q.GetNumber())-1)//2;xy=[45.7 if int(q.GetNumber())%2 else 41.7,24.6-.8*i]
 assert math.dist([p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)],xy)<.00001
 out.append({'pin':q.GetNumber(),'net':q.GetNetname(),'xy_mm':[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)]})
report={'status':'PASS_LOGICAL_XY_AND_SMT_GEOMETRY_NOT_ASSEMBLY_RELEASE','checks':out,'pins_checked':20,'mismatches':0,'pcb_sha256':sources,'footprint_sha256':footprints,'pitch_mm':.8,'pcb_surface_gap_mm':8.5,'drawing_mated_height_tolerance_mm':.15,'female_height_grade_mm':4.5,'male_height_grade_mm':4.0,'electrical_drills':0,'plastic_locator_holes_per_board':2,'digital_F_side_metal_tail_protrusion_mm':0,'z_reference_mm':{'afe_bottom':0,'afe_top':1.6,'female_nominal_top':6.1,'digital_bottom':10.1,'digital_top':11.7,'male_nominal_housing_low':6.1,'male_nominal_contact_tip':4.2},'scope':'Native logical pad XY/net and surface keepout checks. Manufacturer drawing does not number contacts. Plastic pegs remain within a 1.6mm PCB; no metal THT tails. 8.5mm is a drawing grade, not a measured assembly gap. Delivered pair, tolerances, supports, insertion and solder joints remain unqualified.'}
(R/'review/interboard_xy_check.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('20 SMT contact pairs and surface keepouts checked; 8.5mm drawing mating height')

from pathlib import Path
import pcbnew as p,wx,json,math,hashlib
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'digital';path=D/'YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='U1801');rules=list(f.Zones());assert len(rules)==1;z=rules[0];assert z.GetIsRuleArea() and z.GetDoNotAllowCopperPour() and not z.GetDoNotAllowTracks() and not z.GetDoNotAllowVias() and not z.GetDoNotAllowPads();assert z.GetZoneName()=='SCH16T_UNDERBODY_NO_POUR';enabled=set(b.GetEnabledLayers().CuStack());assert enabled<=set(z.GetLayerSet().Seq())
outline=z.Outline().COutline(0);pts=[[p.ToMM(outline.CPoint(i).x),p.ToMM(outline.CPoint(i).y)] for i in range(outline.PointCount())];bounds=[min(q[0] for q in pts),min(q[1] for q in pts),max(q[0] for q in pts),max(q[1] for q in pts)];assert all(abs(a-c)<1e-6 for a,c in zip(bounds,[25.2,1.8,36.,15.2]));rows=[]
for ly in enabled:
 pours=[zz for zz in b.Zones() if not zz.GetIsRuleArea() and zz.IsOnLayer(ly)];covered=0;count=0
 for ix in range(108):
  for iy in range(134):
   point=p.VECTOR2I(p.FromMM(25.25+ix*.1),p.FromMM(1.85+iy*.1));count+=1
   if any(zz.GetFilledPolysList(ly).Contains(point) for zz in pours):covered+=1
 rows.append(dict(layer=b.GetLayerName(ly),samples=count,pour_covered_samples=covered));assert covered==0,(b.GetLayerName(ly),covered)
q=dict(status='NATIVE_RULE_AND_FILLED_POUR_SCREEN_PASS_NOT_PERFORMANCE_VALIDATION',pcb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rule_attached_to='U1801',footprint_library_sha256=hashlib.sha256((H/'footprints/YuEEG_IMU.pretty/Murata_SCH16T_SOIC24_14p20x9p30_P0p80.kicad_mod').read_bytes()).hexdigest(),global_bounds_mm=bounds,local_body_envelope_mm=[-5.4,-6.7,5.4,6.7],rules=dict(copperpour_forbidden=True,tracks_allowed=True,vias_allowed=True,pads_allowed=True),layers=rows,source='https://sensorsandpower.angst-pfister.com/fileadmin/products/datasheets/191/SCH16T-K01-rev6_1630-21648-0045-E-1125.pdf',source_section='Murata Doc11624 Rev6 section8.2, publicly indexed excerpt. No direct fullPDF download or possession claim.',scope='Native footprint rule follows move/flip/rotation; all6Cu covered. Filled-pour sampling at0.1mm pitch inside its rectangle, not a proof of field performance or complete continuous-area topology. Routed GND lines/vias under body are explicitly permitted by the reviewed manufacturer recommendation.')
(D/'review/imu_underbody_rule_check.json').write_text(json.dumps(q,indent=2),encoding='utf8');print('Underbody native rule and fill screen passed',rows)

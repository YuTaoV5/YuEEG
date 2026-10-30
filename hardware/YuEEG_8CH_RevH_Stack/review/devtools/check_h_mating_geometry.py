from pathlib import Path
import pcbnew as p,wx,json
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack');fs={}
for name in ['afe','digital']:
 b=p.LoadBoard(str(R/name/('YuEEG_H_'+name.upper()+'.kicad_pcb')));f=next(f for f in b.GetFootprints() if f.GetReference()=='JH1');fs[name]=(b,f)
out=[];a={q.GetNumber():q for q in fs['afe'][1].Pads()}
for q in fs['digital'][1].Pads():
 other=a[q.GetNumber()];assert q.GetNetname()==other.GetNetname();assert (q.GetPosition()-other.GetPosition()).EuclideanNorm()<p.FromMM(.001);assert abs(p.ToMM(q.GetDrillSize().x)-.9)<.0001
 out.append({'pin':q.GetNumber(),'net':q.GetNetname(),'xy_mm':[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)]})
gap=8.5;female=6.35;male=1.5;post=4;insertion=post-(gap-female-male);assert 2.62<insertion<5.03
(R/'review/interboard_xy_check.json').write_text(json.dumps({'checks':out,'pins_checked':20,'mismatches':0,'pcb_surface_gap_mm':gap,'nominal_insertion_mm':insertion,'insertion_range_mm':[2.62,5.03],'z_reference_mm':{'afe_bottom':0,'afe_top':1.6,'socket_top':7.95,'digital_bottom':10.1,'digital_top':11.7,'male_body_low':8.6,'male_post_tip':4.6,'digital_solder_tail_tip':12.8},'scope':'Native assembled XY and electrical net mapping; nominal connector dimensions from manufacturer. Does not certify full assembly, supplier part tolerances, FPC fit or enclosure isolation.'},indent=2));print('20 pin XY/net pairs checked; insertion',insertion,'mm')

"""Compare current SPI2 centerline samples with the pre-SMT native ground fill.

This screens filled copper at sampled XY only, never signal integrity or EEG noise.
Pass the actual pre-migration board; its digest must match the adoption record.
"""
from pathlib import Path
import sys,json,hashlib,math,pcbnew as p,wx
wx.DisableAsserts()
H=Path('hardware/YuEEG_8CH_RevH_Stack');path=H/'digital/YuEEG_H_DIGITAL.kicad_pcb'
baseline=Path(sys.argv[1]);adopt=json.loads((H/'review/smt_btb_adoption.json').read_text(encoding='utf8'))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(baseline)==adopt['boards']['digital']['baseline_pcb_sha256']
b=p.LoadBoard(str(path));old=p.LoadBoard(str(baseline));rows={}
def covered(board,pt,ly):
 return any(z.GetFilledPolysList(ly).Contains(pt) for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(ly) and z.HasFilledPolysForLayer(ly))
for net in ['ADS_CS','ADS_SCLK','ADS_MOSI','ADS_MISO','ADS_DRDY','ADS_RESET','ADS_START','ADS_PWDN']:
 row={'planar_length_mm':0,'samples':0,'missing_all_reference_samples':0,'missing_length_estimate_mm':0,'current_missing_but_baseline_plane_present_samples':0,'missing_outside_signal_antipads_samples':0,'missing_examples_mm':[]}
 vias=[t for t in b.GetTracks() if t.Type()==p.PCB_VIA_T and t.GetNetname()!='GND']
 for t in b.GetTracks():
  if t.Type()==p.PCB_VIA_T or t.GetNetname()!=net:continue
  ly=t.GetLayer();refs=[p.In1_Cu] if ly==p.F_Cu else [p.In3_Cu] if ly in [p.B_Cu,p.In4_Cu] else [p.In1_Cu,p.In3_Cu]
  length=p.ToMM(t.GetLength());row['planar_length_mm']+=length;steps=max(1,math.ceil(length/.1));a,c=t.GetStart(),t.GetEnd()
  for i in range(steps):
   f=(i+.5)/steps;pt=p.VECTOR2I(round(a.x+(c.x-a.x)*f),round(a.y+(c.y-a.y)*f));row['samples']+=1
   if any(covered(b,pt,r) for r in refs):continue
   row['missing_all_reference_samples']+=1;row['missing_length_estimate_mm']+=length/steps
   if any(covered(old,pt,r) for r in refs):row['current_missing_but_baseline_plane_present_samples']+=1
   near=any((t.GetPosition()-pt).EuclideanNorm()<=t.GetWidth(p.In1_Cu)/2+p.FromMM(.18) for t in vias)
   if not near:
    row['missing_outside_signal_antipads_samples']+=1
    if len(row['missing_examples_mm'])<8:row['missing_examples_mm'].append([p.ToMM(pt.x),p.ToMM(pt.y),b.GetLayerName(ly)])
 rows[net]=row
out={'status':'NATIVE_CENTERLINE_SCREEN_NOT_SIGNAL_INTEGRITY_VALIDATION','pcb_sha256':sha(path),'baseline_pcb_sha256':sha(baseline),'baseline_revision':'b67843f before SMT migration','sample_pitch_max_mm':.1,'nets':rows,'scope':'Midpoint samples, length-weighted missing copper estimate; reference F=In1, B/In4=In3, In2=In1 or In3. No proof of connected return path around holes, full trace width, impedance, edge ringing, crosstalk, ADC timing or EEG noise. Baseline coverage queried at CURRENT route XY, not a comparison of equal-length old/new traces.'}
(H/'digital/review/smt_spi2_reference_screen.json').write_text(json.dumps(out,indent=2),encoding='utf8')
for net,row in rows.items():print(net,'length',round(row['planar_length_mm'],2),'missing_mm',round(row['missing_length_estimate_mm'],3),'outside_antipads',row['missing_outside_signal_antipads_samples'])

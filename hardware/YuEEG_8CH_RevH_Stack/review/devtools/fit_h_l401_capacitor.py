from pathlib import Path
import sys,json
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');lib=R/'footprints/YuEEG.pretty/TDK_SPM4015_LR.kicad_mod'
paths=[lib,R/'digital/YuEEG_H_DIGITAL.kicad_pcb',R/'power/YuEEG_H_POWER.kicad_pcb']
for path in paths:
 d=loads(path.read_text());fps=[d] if path==lib else [q for q in d if isinstance(q,list) and q[0]=='footprint']
 for f in fps:
  if path==lib:ref=None
  else:ref=next(json.loads(q[2]) for q in f if isinstance(q,list) and q[0]=='property' and q[1]=='"Reference"')
  if path!=lib and not (path.parent.name=='digital' and ref=='L401' or path.parent.name=='power' and ref=='LP1'):
   if path.parent.name=='digital' and ref=='C407':sub(f,'at')[1:]=['25','38.3','0']
   continue
  # 4.1+0.2 maximum body width plus .25mm courtyard allowance on each side.
  for q in f:
   if isinstance(q,list) and q[0]=='fp_rect' and sub(q,'layer')[1]=='"F.CrtYd"':sub(q,'start')[2]='-2.4';sub(q,'end')[2]='2.4'
  if ref=='L401':sub(f,'at')[1:]=['24.9','33.65','-90']
 path.write_text(dumps(d))
# Raw footprint rotation also requires pad and local graphic rotations. Let pcbnew do it
# from the original 0-degree L401 footprint, rather than modifying only the parent.
import pcbnew as p,wx
wx.DisableAsserts();path=R/'digital/YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
# The parser has transformed all children using the new parent rotation on load.
assert abs(fs['L401'].GetOrientationDegrees()+90)<.001
# Pad orientation was serialized at zero before the parent-only edit; align rects.
for f in [fs['L401'],fs['C407']]:
 for q in f.Pads():q.SetOrientationDegrees(f.GetOrientationDegrees())
p.SaveBoard(str(path),b)
source=Path('logs/layout_h_1s_power.py');source.write_text(source.read_text().replace('(start -2.75 -2.5) (end 2.75 2.5)','(start -2.75 -2.4) (end 2.75 2.4)'))
print('Placed selected L401 vertically; rotated output capacitor for clearance within same board')

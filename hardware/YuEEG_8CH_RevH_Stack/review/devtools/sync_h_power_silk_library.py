from pathlib import Path
import sys,pcbnew as p
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');path=R/'power/YuEEG_H_POWER.kicad_pcb';b=p.LoadBoard(str(path))
for ref,lib,name in [('SWP1','Button_Switch_SMD','SW_SPDT_PCM12'),('JP1','Connector_PinHeader_2.00mm','PinHeader_1x02_P2.00mm_Vertical')]:
 f=next(f for f in b.GetFootprints() if f.GetReference()==ref)
 for g in f.GraphicalItems():
  if g.GetLayer()==p.F_SilkS:g.SetLayer(p.F_Fab)
 fp=R/'footprints'/(lib+'.pretty')/(name+'.kicad_mod');d=loads(fp.read_text())
 for g in d:
  if isinstance(g,list) and g[0].startswith('fp_'):
   layer=sub(g,'layer')
   if layer and layer[1]=='"F.SilkS"':layer[1]='"F.Fab"'
 fp.write_text(dumps(d))
p.SaveBoard(str(path),b);print('Power body outlines and project footprint library agree')

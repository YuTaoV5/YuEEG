from pathlib import Path
import sys,json
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');base=Path('X:/SoftWare/Kicad/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty/PinHeader_1x10_P2.54mm_Horizontal.kicad_mod')
d=loads(base.read_text());d[1]='"Electrode_1x10_Horizontal_ReverseLogical"'
for node in d:
 if not isinstance(node,list):continue
 if node[0]=='pad':
  number=11-int(json.loads(node[1]));node[1]=json.dumps(str(number));node[3]='rect' if number==1 else 'oval'
 if node[0].startswith('fp_') and sub(node,'layer') and sub(node,'layer')[1]=='"F.SilkS"':sub(node,'layer')[1]='"F.Fab"'
(R/'footprints/YuEEG.pretty/Electrode_1x10_Horizontal_ReverseLogical.kicad_mod').write_text(dumps(d))
print('Side electrode footprint prepared; logical order reversed before 180-degree mounting')

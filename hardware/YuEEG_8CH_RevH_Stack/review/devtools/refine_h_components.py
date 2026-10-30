from pathlib import Path
import json,sys,copy
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');O=Path('hardware/YuEEG_8CH_RevH/footprints/YuEEG.pretty');D=R/'footprints/YuEEG.pretty';Q=json.dumps
current=D/'ALPS_SKRTLBE010_GroundedShell.kicad_mod'
if current.exists():
 # Preserve the later manufacturer's copper prohibition and dimensional model.
 sw=loads(current.read_text())
else:
 sw=loads((O/'ALPS_SKRTLAE010_GroundedShell.kicad_mod').read_text());sw[1]=Q('ALPS_SKRTLBE010_GroundedShell')
 sw[:]=[x for x in sw if not(isinstance(x,list) and (x[0]=='model' or (x[0]=='pad' and x[2]=='np_thru_hole')))]
(D/'ALPS_SKRTLBE010_GroundedShell.kicad_mod').write_text(dumps(sw))
sd=loads((O/'KINGCONN_7TFCN_FA_1010_C.kicad_mod').read_text());sd[1]=Q('KINGCONN_7TFCN_FA_1010_C_NotchedShield')
sd[:]=[x for x in sd if not(isinstance(x,list) and x[0]=='pad' and json.loads(x[1])=='11' and sub(x,'at')[1]=='4.95')]
poly=[[-.9,-2.7],[.9,-2.7],[.9,.4],[.35,1.3],[.35,2.7],[-.35,2.7],[-.35,1.3],[-.9,.4]]
sd.append(['pad','"11"','smd','custom',['at','4.95','-2.7'],['size','.5','.5'],['layers','"F.Cu"','"F.Paste"','"F.Mask"'],['options',['clearance','outline'],['anchor','rect']],['primitives',['gr_poly',['pts',*([ 'xy',str(x),str(y)] for x,y in poly)],['width','0'],['fill','yes']]]])
(D/'KINGCONN_7TFCN_FA_1010_C_NotchedShield.kicad_mod').write_text(dumps(sd))
(R/'review/component_decisions.json').write_text(json.dumps({'switch':{'part':'ALPS SKRTLBE010','source':'https://tech.alpsalpine.com/e/products/detail/SKRTLBE010/','height_mm':3.3,'force_N':1.6,'bosses':False,'note':'Grounded support pads; old LAE 3D model removed because it contains guide bosses.'},'microSD':{'part':'KINGCONN 7TFCN-FA-1010-C','source':'https://www.kingconn.com.tw/files/7TFCN-FA-1010-X.pdf','height_mm':3.75,'card_underside_mm':2.56,'under_card_part_height_limit_mm':1.2,'note':'Ground land neck is an engineering adaptation of the manufacturer tapered land: .7mm neck instead of the invalid rectangular overlap with pad 8. Solder/contact geometry still requires supplier confirmation. Must verify with card and socket samples.'}},indent=2))
print('Refined side-switch and notched short-body SD footprints')

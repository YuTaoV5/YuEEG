from pathlib import Path
import json,sys,uuid
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack')
for board in ['afe','digital','power']:
 path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');d=loads(path.read_text())
 nets={json.loads(z[2]):z[1] for z in d if isinstance(z,list) and z[0]=='net'}
 specs=[('AFE_GND_PLANE','GND','In1.Cu',(0.4,.4,47.6,59.6),0)] if board=='afe' else [('POWER_GND','GND','B.Cu',(.4,.4,33.6,17.6),0),('POWER_RTN_THERMAL','P_RTN','B.Cu',(17,3,28,11.5),1)]
 if board=='digital':specs=[('DIGITAL_GND_'+layer,'GND',layer,(.4,.4,47.6,40.5),0) for layer in ['In1.Cu','In3.Cu']]+[('HOST_GND_'+layer,'HOST_GND',layer,(.4,49.1,47.6,59.6),0) for layer in ['In1.Cu','In3.Cu']]
 names={name for name,*_ in specs}
 d[:]=[z for z in d if not(isinstance(z,list) and z[0]=='zone' and sub(z,'name') and json.loads(sub(z,'name')[1]) in names)]
 for name,net,layer,(x0,y0,x1,y1),priority in specs:
  d.append(['zone',['net',nets[net]],['net_name',json.dumps(net)],['layer',json.dumps(layer)],['uuid',json.dumps(str(uuid.uuid4()))],['name',json.dumps(name)],['hatch','edge','.5'],['priority',str(priority)],['connect_pads','yes',['clearance','.15']],['min_thickness','.15'],['filled_areas_thickness','no'],['fill','yes',['thermal_gap','.2'],['thermal_bridge_width','.25']],['polygon',['pts',*(['xy',str(x),str(y)] for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)])]]])
 path.write_text(dumps(d));print(board,'ground zones defined')

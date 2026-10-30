from pathlib import Path
import sys,json,uuid,math
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
path=Path('logs/RevH_DigitalCandidate/YuEEG_H_DIGITAL.kicad_pcb');b=loads(path.read_text(encoding='utf8'))
b[:]=[g for g in b if not(isinstance(g,list) and (g[0] in ['gr_line','gr_arc'] and sub(g,'layer') and sub(g,'layer')[1]=='"Edge.Cuts"' or g[0]=='zone' and sub(g,'name') and json.loads(sub(g,'name')[1]).startswith('H_CAND_')))]
def edge(kind,pts):
 b.append([kind,*([n,str(x),str(y)] for n,(x,y) in pts),['stroke',['width','.05'],['type','default']],['layer','"Edge.Cuts"'],['uuid',json.dumps(str(uuid.uuid4()))]])
for a,c in [((2,0),(46,0)),((48,2),(48,58)),((46,60),(2,60)),((0,58),(0,2))]:edge('gr_line',[('start',a),('end',c)])
for a,m,c in [((46,0),(47.414214,.585786),(48,2)),((48,58),(47.414214,59.414214),(46,60)),((2,60),(.585786,59.414214),(0,58)),((0,2),(.585786,.585786),(2,0))]:edge('gr_arc',[('start',a),('mid',m),('end',c)])
def keep(name,pts):
 b.append(['zone',['net','0'],['net_name','""'],['layers',*map(json.dumps,['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'])],['uuid',json.dumps(str(uuid.uuid4()))],['name',json.dumps('H_CAND_'+name)],['hatch','edge','.5'],['connect_pads',['clearance','0']],['min_thickness','.15'],['filled_areas_thickness','no'],['keepout',['tracks','not_allowed'],['vias','not_allowed'],['pads','not_allowed'],['copperpour','not_allowed'],['footprints','allowed']],['fill',['thermal_gap','.3'],['thermal_bridge_width','.3']],['polygon',['pts',*(['xy',str(x),str(y)] for x,y in pts)]]])
keep('USB_BARRIER',[(0,40.55),(48,40.55),(48,49.05),(0,49.05)])
for name,x0,y0,x1,y1 in [('L',0,0,.3,60),('R',47.7,0,48,60),('T',0,0,48,.3),('B',0,59.7,48,60)]:keep('EDGE_'+name,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
base=[(0,0),(2,0),(2,.35)]+[(2+1.65*math.cos(t),2+1.65*math.sin(t)) for t in [math.radians(-90-i*90/12) for i in range(1,13)]]+[(0,2)]
for i,fun in enumerate([lambda x,y:(x,y),lambda x,y:(48-x,y),lambda x,y:(48-x,60-y),lambda x,y:(x,60-y)]):keep('CORNER_'+str(i),[fun(x,y) for x,y in base])
path.write_text(dumps(b),encoding='utf8');print('Rounded outline, six-layer isolation and edge guards applied')

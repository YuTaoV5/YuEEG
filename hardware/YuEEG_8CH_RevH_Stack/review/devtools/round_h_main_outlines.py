from pathlib import Path
import sys,json,uuid,math
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack')
for board,W,H,r in [('afe',48,60,2),('power',34,18,1)]:
 path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');b=loads(path.read_text())
 b[:]=[g for g in b if not(isinstance(g,list) and g[0] in ['gr_line','gr_arc'] and sub(g,'layer') and sub(g,'layer')[1]=='"Edge.Cuts"')]
 def edge(kind,pts):b.append([kind,*([n,str(x),str(y)] for n,(x,y) in pts),['stroke',['width','.05'],['type','default']],['layer','"Edge.Cuts"'],['uuid',json.dumps(str(uuid.uuid4()))]])
 for a,c in [((r,0),(W-r,0)),((W,r),(W,H-r)),((W-r,H),(r,H)),((0,H-r),(0,r))]:edge('gr_line',[('start',a),('end',c)])
 d=r/math.sqrt(2)
 for a,m,c in [((W-r,0),(W-r+d,r-d),(W,r)),((W,H-r),(W-r+d,H-r+d),(W-r,H)),((r,H),(r-d,H-r+d),(0,H-r)),((0,r),(r-d,r-d),(r,0))]:edge('gr_arc',[('start',a),('mid',m),('end',c)])
 path.write_text(dumps(b));print(board,'rounded',W,H,'R',r)

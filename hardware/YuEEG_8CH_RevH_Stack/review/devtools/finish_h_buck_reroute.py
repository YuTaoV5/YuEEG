from pathlib import Path
import json,sys
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';b=loads(path.read_text());nc=next(z[1] for z in b if isinstance(z,list) and z[0]=='net' and json.loads(z[2])=='STATUS_FAULT_A')
b[:]=[z for z in b if not(isinstance(z,list) and z[0] in ['segment','via','arc'] and sub(z,'net') and sub(z,'net')[1]==nc)]
# Adjust module frame boundaries to include the new B-side input capacitor.
for z in b:
 if not(isinstance(z,list) and z[0]=='gr_line' and sub(z,'layer') and sub(z,'layer')[1]=='"B.Silkscreen"'):continue
 for name in ['start','end']:
  q=sub(z,name);y=float(q[2])
  if abs(y-24.8)<.001:q[2]='23.8'
  elif abs(y-26)<.001:q[2]='27.5'
path.write_text(dumps(b))
s=Path('logs/route_h_digital.py').read_text().replace("=='In1.Cu'","in ['In1.Cu','In3.Cu']")
exec(s)

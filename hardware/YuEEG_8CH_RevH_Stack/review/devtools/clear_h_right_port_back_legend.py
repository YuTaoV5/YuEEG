"""Move only the back power legend off the new through-hole solder pads."""
from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
D=Path('logs/right_power_port_candidate');path=D/'YuEEG_H_DIGITAL.kicad_pcb';t=loads(path.read_text(encoding='utf8'));matches=[v for v in t if isinstance(v,list) and v[0]=='gr_text' and json.loads(v[1])=='3V3 / POWER' and sub(v,'layer')[1]=='"B.SilkS"'];assert len(matches)==1;sub(matches[0],'at')[1]='27';path.write_text(dumps(t),encoding='utf8');subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--format','json','-o',str(D/'drc.json'),str(path)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);d=json.loads((D/'drc.json').read_text());print('Candidate final: DRC',len(d['violations']),'unconnected',len(d['unconnected_items']));assert not d['violations'] and not d['unconnected_items']

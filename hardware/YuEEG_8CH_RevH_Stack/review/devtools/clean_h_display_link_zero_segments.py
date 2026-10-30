"""Remove only zero-length grid-escape artifacts; do not trim real copper."""
from pathlib import Path
import sys,json,math,subprocess
sys.path.insert(0,str(Path('hardware/YuEEG_8CH_RevG/review').resolve()));from sexpr_io import loads,dumps,sub
D=Path('hardware/YuEEG_8CH_RevH_Stack/display_link');path=D/'YuEEG_H_DISPLAY_LINK.kicad_pcb';tree=loads(path.read_text());kept=[];removed=0
for item in tree:
 if isinstance(item,list) and item[0]=='segment' and math.dist(list(map(float,sub(item,'start')[1:])),list(map(float,sub(item,'end')[1:])))<1e-6:removed+=1
 else:kept.append(item)
path.write_text(dumps(kept));report=D/'review/drc_current.json';subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','-o',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);d=json.loads(report.read_text(encoding='utf8'));print('Removed',removed,'zero-length artifacts; DRC',len(d['violations']),'unconnected',len(d['unconnected_items']),'parity',len(d['schematic_parity']));assert not any(d[k] for k in ['violations','unconnected_items','schematic_parity'])

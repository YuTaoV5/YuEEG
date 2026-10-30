from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
path=Path('hardware/YuEEG_8CH_RevH_Stack/digital/YuEEG_H_DIGITAL.kicad_pcb');original=path.read_bytes();d=loads(path.read_text());nets={n[1]:json.loads(n[2]) for n in d if isinstance(n,list) and n[0]=='net'};changed=[]
for t in d:
 if not(isinstance(t,list) and t[0]=='segment' and nets[sub(t,'net')[1]]=='+3V3' and sub(t,'layer')[1]=='"F.Cu"'):continue
 pts=[tuple(map(float,sub(t,q)[1:])) for q in ['start','end']]
 if all(23.35<=x<=25 and 36.5<=y<=38.5 for x,y in pts):
  sub(t,'width')[1]='.4';changed.append(json.loads(sub(t,'uuid')[1]))
assert changed
path.write_text(dumps(d));report=path.parent/'review/drc_c407_width.json';subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','--output',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);check=json.loads(report.read_text())
if check['violations'] or check['unconnected_items'] or check['schematic_parity']:
 path.write_bytes(original);raise RuntimeError('Widening failed native DRC; restored original PCB')
(path.parent/'review/c407_link_width.json').write_text(json.dumps({'width_mm':.4,'segments':changed,'scope':'Output capacitor local connection; native DRC checked, physical transient validation pending.'},indent=2));print('C407 local supply link widened to .4mm:',len(changed),'segments')

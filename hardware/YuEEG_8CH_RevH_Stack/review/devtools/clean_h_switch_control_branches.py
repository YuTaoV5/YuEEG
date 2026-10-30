from pathlib import Path
import sys,json
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';d=loads(path.read_text());nets={n[1]:json.loads(n[2]) for n in d if isinstance(n,list) and n[0]=='net'};report=json.loads((R/'review/drc_current.json').read_text(encoding='utf8'));bad={i['uuid'] for v in report['violations'] if v['type']=='items_not_allowed' for i in v['items']};removed=[]
for z in list(d):
 if not(isinstance(z,list) and z[0] in ['segment','via','arc']):continue
 uid=json.loads(sub(z,'uuid')[1]);net=nets[sub(z,'net')[1]];layer=sub(z,'layer')
 if net=='ESP_BOOT' or uid in bad or layer and json.loads(layer[1]) in ['In1.Cu','In3.Cu'] and net not in ['GND','HOST_GND']:
  d.remove(z);removed.append({'uuid':uid,'net':net,'layer':layer[1] if layer else 'through via'})
path.write_text(dumps(d));(R/'review/switch_control_branch_cleanup.json').write_text(json.dumps(removed,indent=2));print('Removed',len(removed),'old boot/control branches and non-ground plane traces')

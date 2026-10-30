from pathlib import Path
import sys,json
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');model='${KIPRJMOD}/../models/ESP32-S3-WROOM-1U.step'
def align(m):
 m[1]=json.dumps(model);sub(sub(m,'offset'),'xyz')[1:]=['-9','-9.6','0']
fp=R/'footprints/RF_Module.pretty/ESP32-S3-WROOM-1U.kicad_mod';d=loads(fp.read_text());align(sub(d,'model'));fp.write_text(dumps(d))
path=R/'digital/YuEEG_H_DIGITAL.kicad_pcb';b=loads(path.read_text())
for f in b:
 if not isinstance(f,list) or f[0]!='footprint':continue
 props={json.loads(x[1]):x for x in f if isinstance(x,list) and x[0]=='property'}
 if json.loads(props['Reference'][2])=='U2':align(sub(f,'model'))
path.write_text(dumps(b));(R/'models/ESP32-S3-WROOM-1U.source.json').write_text(json.dumps({'source':'https://www.espressif.com/sites/default/files/3dmodel/ESP32-S3-WROOM-1U%203D%20Model.STEP','provider':'Espressif official module page','download_date':'2026-10-30','alignment_status':'native render check pending; original manufacturer coordinates'},indent=2))

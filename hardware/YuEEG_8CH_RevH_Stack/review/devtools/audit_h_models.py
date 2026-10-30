from pathlib import Path
import sys,json,csv
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');out=[]
for board in ['afe','digital','power']:
 for f in loads((R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb')).read_text()):
  if not isinstance(f,list) or f[0]!='footprint':continue
  props={json.loads(z[1]):json.loads(z[2]) for z in f if isinstance(z,list) and z[0]=='property'}
  models=[json.loads(z[1]) for z in f if isinstance(z,list) and z[0]=='model'];resolved=[Path(m.replace('${KIPRJMOD}',(R/board).resolve().as_posix()).replace('${KICAD9_3DMODEL_DIR}','X:/SoftWare/Kicad/share/kicad/3dmodels')) for m in models]
  out.append({'board':board,'reference':props['Reference'],'value':props['Value'],'models':models,'existing':[p.exists() for p in resolved],'available_wrl_alternative':[p.with_suffix('.wrl').exists() for p in resolved]})
(R/'review/model_audit.json').write_text(json.dumps(out,indent=2));print(*[x for x in out if not x['models'] or not all(x['existing'])],sep='\n')

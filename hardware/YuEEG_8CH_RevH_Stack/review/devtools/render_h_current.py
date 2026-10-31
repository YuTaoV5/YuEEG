from pathlib import Path
import subprocess,json,hashlib,re
R=Path('hardware/YuEEG_8CH_RevH_Stack').resolve();records=[]
for board,side in [('afe','top'),('digital','bottom'),('digital','top'),('power','top')]:
 source=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');s=source.read_text();prefix='${KIPRJMOD}/../models/'
 # CLI 9.0.5 did not load these project-relative local models in a bare PCB render.
 # Change paths only in a disposable rendering copy; the authoritative PCB stays portable.
 temp=Path('logs')/(board+'_render_copy.kicad_pcb');temp.write_text(s.replace(prefix,(R/'models').as_posix()+'/'))
 with (Path('logs')/('render_current_'+board+'.stdout')).open('w') as out,(Path('logs')/('render_current_'+board+'.stderr')).open('w') as err:
  subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','render','--output',str(R/board/'review'/(side+'_current.png')),'--width','1400' if board=='power' else '1000','--height','800' if board=='power' else '1200','--side',side,'--background','opaque','--quality','basic',str(temp)],stdout=out,stderr=err,check=True)
 records.append({'board':board,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'side':side,'local_model_path_substitutions':s.count(prefix),'referenced_local_model_sha256':{name:hashlib.sha256((R/'models'/name).read_bytes()).hexdigest() for name in sorted(set(re.findall(r'\(model\s+"\$\{KIPRJMOD\}/\.\./models/([^"]+)"',s)))},'scope':'Rendering copy differs only by absolute local model paths. Main PCB/library keep project-relative paths. Missing models in model_audit.json remain absent.'})
(R/'review/render_evidence.json').write_text(json.dumps(records,indent=2));print('Rendered current boards with explicitly resolved local model paths')

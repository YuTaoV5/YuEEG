"""Make the Rev H design portable and compare embedded symbols with local libraries."""
from pathlib import Path
import sys,json,csv,copy,shutil
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');L=Path('X:/SoftWare/Kicad/share/kicad/footprints')
symbols={};fps={}
for board in ['afe','digital','power']:
 for f in (R/board).glob('*.kicad_sch'):
  for s in (sub(loads(f.read_text(encoding='utf8')),'lib_symbols') or [])[1:]:
   key=json.loads(s[1]);old=symbols.get(key)
   if old is not None:assert old==s,('Conflicting symbol definitions',key,f)
   symbols[key]=copy.deepcopy(s)
 for row in csv.DictReader((R/board/'BOM.csv').open(encoding='utf-8-sig')):
  key=row['Footprint'];lib,name=key.split(':');dest=R/'footprints'/(lib+'.pretty')/(name+'.kicad_mod')
  if not dest.exists():
   dest.parent.mkdir(exist_ok=True);shutil.copy2(L/(lib+'.pretty')/(name+'.kicad_mod'),dest)
  fps[key]=True
 # Include native mechanical drill features without adding fake electronic BOM rows.
 for f in loads((R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb')).read_text()):
  if not(isinstance(f,list) and f[0]=='footprint' and 'board_only' in (sub(f,'attr') or [])):continue
  key=json.loads(f[1]);lib,name=key.split(':');dest=R/'footprints'/(lib+'.pretty')/(name+'.kicad_mod')
  if not dest.exists():
   dest.parent.mkdir(exist_ok=True);shutil.copy2(L/(lib+'.pretty')/(name+'.kicad_mod'),dest)
  fps[key]=True
groups={}
for key,s in symbols.items():
 lib,name=key.split(':');s[1]=json.dumps(name);groups.setdefault(lib,[]).append(s)
for lib,ss in groups.items():
 text=dumps(['kicad_symbol_lib',['version','20241209'],['generator','"kicad_symbol_editor"'],*ss])
 path=R/'YuEEG.kicad_sym' if lib=='YuEEG' else R/'libraries'/(lib+'.kicad_sym')
 path.write_text(text,encoding='utf8')
fpnames=sorted({key.split(':')[0] for key in fps})
for board in ['afe','digital','power']:
 base=R/board
 base.joinpath('fp-lib-table').write_text(dumps(['fp_lib_table',['version','7'],*[
  ['lib',['name',json.dumps(lib)],['type','"KiCad"'],['uri',json.dumps('${KIPRJMOD}/../footprints/'+lib+'.pretty')],['options','""'],['descr','"Rev H local"']] for lib in fpnames]]))
 base.joinpath('sym-lib-table').write_text(dumps(['sym_lib_table',['version','7'],*[
  ['lib',['name',json.dumps(lib)],['type','"KiCad"'],['uri',json.dumps('${KIPRJMOD}/../'+('YuEEG.kicad_sym' if lib=='YuEEG' else 'libraries/'+lib+'.kicad_sym'))],['options','""'],['descr','"Rev H local"']] for lib in sorted(groups)]]))
print('Libraries:',len(symbols),'symbols;',len(fps),'footprints')

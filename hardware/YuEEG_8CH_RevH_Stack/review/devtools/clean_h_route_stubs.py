from pathlib import Path
import sys,json,subprocess,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');removed=[]
for board in ['afe','digital']:
 path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');report=R/board/'review/drc_current.json'
 for passno in range(20):
  b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
  result=subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','--output',str(report),str(path)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL);assert result.returncode==0,result.stdout
  d=json.loads(report.read_text(encoding='utf8'));ids={i['uuid'] for v in d['violations'] if v['type'] in ['track_dangling','via_dangling'] for i in v['items']}
  if not ids:print(board,'remaining DRC',len(d['violations']),'unconnected',len(d['unconnected_items']),'parity',len(d['schematic_parity']),flush=True);break
  tree=loads(path.read_text());old=len(tree);tree[:]=[z for z in tree if not(isinstance(z,list) and z[0] in ['segment','via','arc'] and sub(z,'uuid') and json.loads(sub(z,'uuid')[1]) in ids)];assert len(tree)<old
  path.write_text(dumps(tree));removed.append({'board':board,'pass':passno,'removed':list(ids)})
(R/'review/stub_cleanup.json').write_text(json.dumps(removed,indent=2))

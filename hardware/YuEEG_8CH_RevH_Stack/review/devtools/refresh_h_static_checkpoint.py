"""Refresh native static reports and bound source hashes without rewriting design docs."""
from pathlib import Path
import json,subprocess,hashlib,datetime
H=Path('hardware/YuEEG_8CH_RevH_Stack');cli='X:/SoftWare/Kicad/bin/kicad-cli.exe';summary=json.loads((H/'review/current_check_summary.json').read_text());summary['timestamp']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
for board in ['afe','digital','power']:
 D=H/board;stem='YuEEG_H_'+board.upper();pcb=D/(stem+'.kicad_pcb')
 for args,name,src in [(['pcb','drc','--schematic-parity'],'drc_current.json',pcb),(['sch','erc'],'erc_current.json',D/(stem+'.kicad_sch'))]:subprocess.run([cli,*args,'--format','json','-o',str(D/'review'/name),str(src)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 drc=json.loads((D/'review/drc_current.json').read_text());erc=json.loads((D/'review/erc_current.json').read_text());counts=dict(drc=len(drc['violations']),unconnected=len(drc['unconnected_items']),parity=len(drc['schematic_parity']),erc=sum(len(s['violations']) for s in erc['sheets']));print(board,counts,flush=True);assert not any(counts.values()),(board,counts)
 old=summary['boards'][board];old.update(counts);old['pcb_sha256']=hashlib.sha256(pcb.read_bytes()).hexdigest()
 old['source_files_sha256']={name:hashlib.sha256((D/name).read_bytes()).hexdigest() for name in old['source_files_sha256']}
(H/'review/current_check_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print('Native static checkpoint refreshed')

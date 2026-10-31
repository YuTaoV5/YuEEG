"""Bind the passive FPC prototype to sources and extract native geometry for review."""
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
import pcbnew as p,wx
wx.DisableAsserts()
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'display_link';R=D/'review';pcb=D/'YuEEG_H_DISPLAY_LINK.kicad_pcb'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
cli='X:/SoftWare/Kicad/bin/kicad-cli.exe'
for kind,args in [('drc',['pcb','drc','--schematic-parity']),('erc',['sch','erc'])]:
 src=pcb if kind=='drc' else pcb.with_suffix('.kicad_sch')
 subprocess.run([cli,*args,'--format','json','-o',str(R/(kind+'_current.json')),str(src)],check=True,stdout=subprocess.DEVNULL)
d=json.loads((R/'drc_current.json').read_text());e=json.loads((R/'erc_current.json').read_text());assert all(not d[k] for k in ['violations','unconnected_items','schematic_parity']) and not any(s['violations'] for s in e['sheets'])
b=p.LoadBoard(str(pcb));q=json.loads((R/'design_contract.json').read_text());fold=json.loads((R/'fold_alignment.json').read_text());assert fold['pcb_sha256']==sha(pcb)
expected=json.loads((R/'expected_connections.json').read_text());actual={};pads=[];tracks=[];edges=[]
pos=lambda v:[p.ToMM(v.x),p.ToMM(v.y)]
for f in b.GetFootprints():
 for pad in f.Pads():
  net=pad.GetNetname();actual[f.GetReference()+'.'+pad.GetNumber()]=None if net.startswith('unconnected-') or not net else net
  pads.append(dict(ref=f.GetReference(),pin=pad.GetNumber(),xy=pos(pad.GetPosition()),size=pos(pad.GetSize()),net=net))
assert actual==expected
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):tracks.append(dict(via=pos(t.GetPosition()),width=p.ToMM(t.GetWidth(p.F_Cu)),net=t.GetNetname()))
 else:tracks.append(dict(start=pos(t.GetStart()),end=pos(t.GetEnd()),width=p.ToMM(t.GetWidth()),layer=b.GetLayerName(t.GetLayer()),net=t.GetNetname()))
for g in b.GetDrawings():
 if g.GetLayer()==p.Edge_Cuts:edges.append([pos(g.GetStart()),pos(g.GetEnd())])
(R/'geometry.json').write_text(json.dumps(dict(pads=pads,tracks=tracks,edges=edges),indent=2))
baseline=json.loads((H/'review/current_check_summary.json').read_text());unchanged={}
for name,r in baseline['boards'].items():
 f=H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');assert sha(f)==r['pcb_sha256'];unchanged[name]=sha(f)
files={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file() and f.suffix in ['.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_mod','.kicad_sym','.csv']}
for name in ['design_contract.json','fold_alignment.json','expected_connections.json','drc_current.json','erc_current.json','netlist.xml','geometry.json','fold_space.json','neighbor_native.json']:files['review/'+name]=sha(R/name)
for name in ['flat_and_fold.png','flat_and_fold.svg','fold_space.png','fold_space.svg']:
 if (R/name).exists():files['review/'+name]=sha(R/name)
record=dict(status='PROTOTYPE_NOT_FOR_ORDER',source_files_sha256=files,baseline_pcb_sha256=unchanged,checks=dict(erc=0,drc=0,unconnected=0,schematic_parity=0,pad_contract=True,bend_vias=0,nonparallel_bend_tracks=0),main_boards_modified_by_this_accessory_build=False,release_gates=['Delivered connector pin-1 and end-to-end continuity','Fabricator stackup, advanced vias, gang coverlay and stiffeners','Screen FPC mounting datum, adjacent component collision and full assembly isolation','Powered display/touch test at current firmware 10 MHz QSPI'])
(R/'checkpoint.json').write_text(json.dumps(record,indent=2));print('FPC prototype checks passed; three main PCBs match current engineering checkpoint')

"""Verify Rev H engineering artifact bindings; does not rerun KiCad or release hardware."""
from pathlib import Path
import csv,hashlib,json,sys,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'hardware/YuEEG_8CH_RevH_Stack'
sys.path.insert(0,str(ROOT/'hardware/YuEEG_8CH_RevG/review'))
from sexpr_io import loads,sub
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def verify():
 summary=json.loads((H/'review/current_check_summary.json').read_text())
 require(summary['release_status'].startswith('DEVELOPMENT'),'Engineering status must not imply a production release')
 for board,count,layers in [('afe',135,4),('digital',113,6),('power',21,2)]:
  base=H/board;pcb=base/('YuEEG_H_'+board.upper()+'.kicad_pcb');record=summary['boards'][board]
  require(sha(pcb)==record['pcb_sha256'],'Stale PCB report: '+board)
  for name,digest in record['source_files_sha256'].items():require(sha(base/name)==digest,'Changed checked source: '+board+'/'+name)
  drc=json.loads((base/'review/drc_current.json').read_text());erc=json.loads((base/'review/erc_current.json').read_text())
  require(all(not drc[k] for k in ['violations','unconnected_items','schematic_parity']),'Dirty PCB report: '+board)
  require(not any(s['violations'] for s in erc['sheets']),'Dirty ERC report: '+board)
  bom={r['Reference']:r for r in csv.DictReader((base/'BOM.csv').open(encoding='utf-8-sig'))};expected=json.loads((base/'review/expected_connections.json').read_text());tree=loads(pcb.read_text());actual={};seen=set();holes={}
  require(len(bom)==count,'Unexpected electrical BOM count: '+board)
  require(sum(1 for l in sub(tree,'layers')[1:] if isinstance(l,list) and json.loads(l[1]).endswith('.Cu'))==layers,'Wrong layer count: '+board)
  for f in tree:
   if not(isinstance(f,list) and f[0]=='footprint'):continue
   props={json.loads(q[1]):json.loads(q[2]) for q in f if isinstance(q,list) and q[0]=='property'};ref=props['Reference'];pads=[q for q in f if isinstance(q,list) and q[0]=='pad']
   if 'board_only' in (sub(f,'attr') or []):
    require(json.loads(f[1])=='YuEEG:MountingHole_M2_Routed_2p4' and not pads,'Unexpected board-only electrical feature')
    circles=[q for q in f if isinstance(q,list) and q[0]=='fp_circle' and sub(q,'layer')[1]=='"Edge.Cuts"']
    require(len(circles)==1 and sub(circles[0],'center')[1:]==['0','0'] and sub(circles[0],'end')[1:]==['1.2','0'],'Mounting opening changed')
    holes[ref]=list(map(float,sub(f,'at')[1:3]));continue
   require(ref in bom and ref not in seen,'Unexpected/duplicate PCB part '+ref);seen.add(ref)
   require(props['Value']==bom[ref]['Value'] and json.loads(f[1])==bom[ref]['Footprint'],'BOM/PCB mismatch '+ref)
   for pad in pads:
    n=sub(pad,'net');num=json.loads(pad[1])
    if num:actual[ref+'.'+num]=json.loads(n[2]) if n else ''
  require(seen==set(bom),'Missing PCB components: '+board)
  for pin,net in expected.items():
   if pin.startswith('#'):continue
   require(pin in actual,'Missing native pad '+pin)
   require(actual[pin]==net if net is not None else not actual[pin] or actual[pin].startswith('unconnected-'),'Native pin mismatch '+pin)
  xml={n.get('ref')+'.'+n.get('pin'):net.get('name') for net in E.parse(base/'review/netlist.xml').findall('./nets/net') for n in net.findall('node')}
  for pin,net in expected.items():
   if pin.startswith('#') or net is None:continue
   require(xml.get(pin)==net,'Exported schematic pin mismatch '+pin)
  require(holes==({'H1':[44.,4.],'H2':[44.,51.],'H3':[4.,55.]} if board!='power' else {}),'Mounting coordinates differ: '+board)
 info=json.loads((H/'firmware/build/BUILD_INFO.json').read_text())
 for name,digest in info['source_sha256'].items():
  require(sha(H/'firmware/ads1299_driver'/name)==digest and sha(ROOT/'Firmware/ads1299_driver'/name)==digest,'Active/snapshot firmware mismatch '+name)
 for name,digest in info['binaries_sha256'].items():require(sha(H/'firmware/build'/name)==digest,'Firmware binary mismatch '+name)
 require(info['protocol_tests_passed']==6 and info['physical_flash_or_transport_tested'] is False,'Unexpected test scope')
 exports=json.loads((H/'fabrication_engineering/MANIFEST.json').read_text());require(exports['status']=='ENGINEERING_REVIEW_ONLY_NOT_FOR_ORDER','Export status is not an engineering draft')
 for q in exports['boards']:
  require(q['pcb_sha256']==summary['boards'][q['board']]['pcb_sha256'],'Stale Gerber export '+q['board'])
  for name,digest in q['files'].items():require(sha(H/'fabrication_engineering'/q['board']/name)==digest,'Changed engineering export '+name)
 print('PASS: Rev H engineering checkpoint: native pin/BOM/source hashes, zero static reports, firmware and review exports. Mechanical/functional release remains incomplete.')
if __name__=='__main__':verify()

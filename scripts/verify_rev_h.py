"""Verify Rev H engineering artifact bindings; does not rerun KiCad or release hardware."""
from pathlib import Path
import csv,hashlib,json,sys,re,xml.etree.ElementTree as E
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
  legends=json.loads((base/'review/module_legends.json').read_text())
  require(legends['source_sha256']==sha(pcb),'Stale module legend evidence: '+board)
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
 geometry=json.loads((H/'digital/review/usb_geometry.json').read_text())
 require(geometry['pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale USB geometry evidence')
 reference=json.loads((H/'digital/review/usb_reference_coverage.json').read_text())
 require(reference['pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale USB reference sampling evidence')
 for render in json.loads((H/'review/render_evidence.json').read_text()):
  require(render['source_sha256']==summary['boards'][render['board']]['pcb_sha256'],'Stale board rendering: '+render['board'])
  require('referenced_local_model_sha256' in render,'Missing rendering model bindings: '+render['board'])
  for name,digest in render['referenced_local_model_sha256'].items():require(sha(H/'models'/name)==digest,'Stale rendered model: '+name)
 battery=H/'mechanical/current/battery_side_envelope.json'
 if battery.exists():
  data=json.loads(battery.read_text());require(data['status']=='CONDITIONAL_MECHANICAL_SCREENING_NOT_ASSEMBLY_RELEASE','Battery screening must not imply assembly release')
  for board,digest in data['baseline_pcb_sha256'].items():require(digest==summary['boards'][board]['pcb_sha256'],'Stale battery envelope source: '+board)
 for name,digest in info['source_sha256'].items():
  require(sha(H/'firmware/ads1299_driver'/name)==digest and sha(ROOT/'Firmware/ads1299_driver'/name)==digest,'Active/snapshot firmware mismatch '+name)
 for name,digest in info['binaries_sha256'].items():require(sha(H/'firmware/build'/name)==digest,'Firmware binary mismatch '+name)
 port=json.loads((H/'digital/review/right_power_port.json').read_text())
 require(port['after_pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale right-facing power port record')
 require(port['pin_map']=={'1':'SYS_5V','2':'BAT_PROTECTED_SENSE','3':'GND','4':'GND'},'Changed PH4 electrical contract')
 ports=json.loads((H/'mechanical/current/power_ports_native.json').read_text())
 for board in ['digital','power']:
  require(ports[board]['pcb_sha256']==summary['boards'][board]['pcb_sha256'],'Stale native power-port extract: '+board)
  require({k:v['net'] for k,v in ports[board]['pads'].items()}==port['pin_map'],'Power cable pin mismatch: '+board)
 require(ports['digital']['xy_mm']==port['position_mm'] and ports['digital']['rotation_deg']==90,'Wrong power port placement')
 header=ports['digital']['interboard_header']
 require(header['pad_centers_mm']['1']==[44.,30.] and header['pad_centers_mm']['20']==[42.,12.],'Stale interboard header projection')
 cable=json.loads((H/'mechanical/current/power_harness_routing_review.json').read_text())
 require(cable['native_ports_sha256']==sha(H/'mechanical/current/power_ports_native.json'),'Stale cable source binding')
 require(cable['native_ports']==ports and cable['status'].endswith('NOT_ASSEMBLY_RELEASE'),'Cable reservation must remain conditional')
 require(cable['display_fpc_pcb_sha256']==sha(H/'display_link/YuEEG_H_DISPLAY_LINK.kicad_pcb'),'Stale cable/FPC binding')
 require(all(w['minimum_signed_gap_mm']>0 for w in cable['current_right_exit_wires']),'Modeled cable overlaps the FPC reservation')
 hb=header['native_pad_bbox_xy_mm'];require(cable['conditional_JH1_post_envelope_mm']==[hb[0],hb[1],0,hb[2],hb[3],1.5],'Cable report uses incorrect header geometry')
 screen=json.loads((H/'mechanical/current/afe_host_screen.json').read_text())
 require(screen['afe_pcb_sha256']==summary['boards']['afe']['pcb_sha256'] and screen['digital_pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale AFE/HOST conditional screen')
 require(screen['afe_copper_y_max_mm']<=47.5001 and screen['c405_minimum_external_host_lower_bound_mm']>8,'AFE conditional screen no longer meets its engineering assumptions')
 change=json.loads((H/'afe/review/power_shadow_change.json').read_text())
 require(change['current_pcb_sha256']=={name:summary['boards'][name]['pcb_sha256'] for name in ['afe','digital']},'Stale analog power change record')
 mouth=json.loads((H/'mechanical/current/usb_mouth_review.json').read_text())
 for name in ['afe','digital']:require(mouth['current_pcb_sha256'][name]==summary['boards'][name]['pcb_sha256'],'Stale USB mouth review: '+name)
 tails=json.loads((H/'mechanical/current/power_port_tail_review.json').read_text())
 require(tails['digital_pcb_sha256']==summary['boards']['digital']['pcb_sha256'] and tails['afe_pcb_sha256']==summary['boards']['afe']['pcb_sha256'],'Stale tail/AFE screening')
 require(tails['status']=='CONDITIONAL_TAIL_SCREEN_NOT_ASSEMBLY_RELEASE' and tails['maximum_tail_solder_projection_allowed_below_digital_mm']==1.2,'Missing conditional tail-trim constraint')
 artifacts=json.loads((H/'mechanical/current/power_harness_artifacts.json').read_text())
 for name,digest in artifacts['files_sha256'].items():require(sha(H/'mechanical/current'/name)==digest,'Changed cable-review artifact: '+name)
 for name,digest in artifacts['pcb_sha256'].items():require(digest==summary['boards'][name]['pcb_sha256'],'Stale cable-review PCB binding: '+name)
 env=json.loads((H/'review/component_envelopes.json').read_text())
 for model in env['models']:require(sha(H/'models'/model['model'])==model['sha256'],'Changed dimensional model: '+model['model'])
 require(info['protocol_tests_passed']==6 and info['physical_flash_or_transport_tested'] is False,'Unexpected test scope')
 selected=json.loads((H/'digital/review/r1101_height_selection.json').read_text())
 require(selected['after_pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale R1101 height selection record')
 require(selected['mpn']=='RC0402FR-0722RL' and selected['body_max_mm']==[1.05,.55,.4] and selected['maximum_mounted_height_for_fold_screen_mm']==.5,'Changed R1101 selected height contract')
 exports=json.loads((H/'fabrication_engineering/MANIFEST.json').read_text());require(exports['status']=='ENGINEERING_REVIEW_ONLY_NOT_FOR_ORDER','Export status is not an engineering draft')
 for q in exports['boards']:
  require(q['pcb_sha256']==summary['boards'][q['board']]['pcb_sha256'],'Stale Gerber export '+q['board'])
  for name,digest in q['files'].items():require(sha(H/'fabrication_engineering'/q['board']/name)==digest,'Changed engineering export '+name)
 drill=(H/'fabrication_engineering/digital/YuEEG_H_DIGITAL-PTH.drl').read_text();tools={};active=None;holes=[]
 require('METRIC' in drill,'Unexpected drill units')
 for line in drill.splitlines():
  definition=re.fullmatch(r'T(\d+)C([\d.]+)',line);selection=re.fullmatch(r'T(\d+)',line);point=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
  if definition:tools[definition[1]]=float(definition[2])
  elif selection:active=selection[1]
  elif point and tools.get(active)==.75:holes.append((float(point[1]),float(point[2])))
 require(sorted(holes)==sorted((v['xy_mm'][0],-v['xy_mm'][1]) for v in ports['digital']['pads'].values()),'PH4 0.75mm plated drill export mismatch')
 with (H/'fabrication_engineering/digital/placement_front.csv').open(encoding='utf8',newline='') as stream:require(all(r['Ref']!='JH2' for r in csv.DictReader(stream)),'TH PH4 must not be listed as an SMT placement')
 if (H/'display_link').exists():
  from verify_display_link import verify as verify_fpc
  verify_fpc()
 print('PASS: Rev H engineering checkpoint: native pin/BOM/source hashes, zero static reports, firmware and review exports. Mechanical/functional release remains incomplete.')
if __name__=='__main__':verify()

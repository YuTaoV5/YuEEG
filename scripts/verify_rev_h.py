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
 summary=json.loads((H/'review/current_check_summary.json').read_text(encoding='utf8'))
 require(summary['release_status'].startswith('DEVELOPMENT'),'Engineering status must not imply a production release')
 for board,count,layers in [('afe',135,4),('digital',129,6),('power',21,2)]:
  base=H/board;pcb=base/('YuEEG_H_'+board.upper()+'.kicad_pcb');record=summary['boards'][board]
  require(sha(pcb)==record['pcb_sha256'],'Stale PCB report: '+board)
  legends=json.loads((base/'review/module_legends.json').read_text(encoding='utf8'))
  require(legends['source_sha256']==sha(pcb),'Stale module legend evidence: '+board)
  for name,digest in record['source_files_sha256'].items():require(sha(base/name)==digest,'Changed checked source: '+board+'/'+name)
  drc=json.loads((base/'review/drc_current.json').read_text(encoding='utf8'));erc=json.loads((base/'review/erc_current.json').read_text(encoding='utf8'))
  require(all(not drc[k] for k in ['violations','unconnected_items','schematic_parity']),'Dirty PCB report: '+board)
  require(not any(s['violations'] for s in erc['sheets']),'Dirty ERC report: '+board)
  bom={r['Reference']:r for r in csv.DictReader((base/'BOM.csv').open(encoding='utf-8-sig'))};expected=json.loads((base/'review/expected_connections.json').read_text(encoding='utf8'));tree=loads(pcb.read_text(encoding='utf8'));actual={};seen=set();holes={}
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
  net_components={n.get('ref'):n for n in E.parse(base/'review/netlist.xml').findall('./components/comp')}
  require(set(net_components)==set(bom),'Netlist component set differs from BOM '+board)
  for ref,row in bom.items():require(net_components[ref].findtext('value')==row['Value'] and net_components[ref].findtext('footprint')==row['Footprint'],'Exported schematic/BOM metadata mismatch '+board+'/'+ref)
  xml={n.get('ref')+'.'+n.get('pin'):net.get('name') for net in E.parse(base/'review/netlist.xml').findall('./nets/net') for n in net.findall('node')}
  for pin,net in expected.items():
   if pin.startswith('#') or net is None:continue
   require(xml.get(pin)==net,'Exported schematic pin mismatch '+pin)
  require(holes==({'H1':[44.,4.],'H2':[44.,51.],'H3':[4.,55.]} if board!='power' else {}),'Mounting coordinates differ: '+board)
 info=json.loads((H/'firmware/build/BUILD_INFO.json').read_text(encoding='utf8'))
 geometry=json.loads((H/'digital/review/usb_geometry.json').read_text(encoding='utf8'))
 require(geometry['pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale USB geometry evidence')
 smt=json.loads((H/'review/smt_btb_adoption.json').read_text(encoding='utf8'));spi2=json.loads((H/'digital/review/smt_spi2_reference_screen.json').read_text(encoding='utf8'))
 for board,record in smt['boards'].items():require(record['pcb_sha256']==summary['boards'][board]['pcb_sha256'] and record['all_other_component_poses_unchanged'] and not record['same_net_smt_hole_clearance_violations'],'Stale/dirty SMT migration record '+board)
 require(spi2['pcb_sha256']==summary['boards']['digital']['pcb_sha256'] and spi2['baseline_pcb_sha256']==smt['boards']['digital']['baseline_pcb_sha256'],'Stale SPI2 reference screen')
 for net in ['ADS_CS','ADS_SCLK','ADS_MOSI','ADS_MISO']:require(spi2['nets'][net]['missing_outside_signal_antipads_samples']==0,'Review changed SPI2 reference copper '+net)
 reference=json.loads((H/'digital/review/usb_reference_coverage.json').read_text(encoding='utf8'))
 require(reference['pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale USB reference sampling evidence')
 for render in json.loads((H/'review/render_evidence.json').read_text(encoding='utf8')):
  require(render['source_sha256']==summary['boards'][render['board']]['pcb_sha256'],'Stale board rendering: '+render['board'])
  require('referenced_local_model_sha256' in render,'Missing rendering model bindings: '+render['board'])
  for name,digest in render['referenced_local_model_sha256'].items():require(sha(H/'models'/name)==digest,'Stale rendered model: '+name)
 battery=H/'mechanical/current/battery_side_envelope.json'
 if battery.exists():
  data=json.loads(battery.read_text(encoding='utf8'));require(data['status']=='CONDITIONAL_MECHANICAL_SCREENING_NOT_ASSEMBLY_RELEASE','Battery screening must not imply assembly release')
  for board,digest in data['baseline_pcb_sha256'].items():require(digest==summary['boards'][board]['pcb_sha256'],'Stale battery envelope source: '+board)
 for name,digest in info['source_sha256'].items():
  require(sha(H/'firmware/ads1299_driver'/name)==digest and sha(ROOT/'Firmware/ads1299_driver'/name)==digest,'Active/snapshot firmware mismatch '+name)
 for name,digest in info['binaries_sha256'].items():require(sha(H/'firmware/build'/name)==digest,'Firmware binary mismatch '+name)
 port=json.loads((H/'digital/review/right_power_port.json').read_text(encoding='utf8'))
 require(port['after_pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale right-facing power port record')
 require(port['pin_map']=={'1':'SYS_5V','2':'BAT_PROTECTED_SENSE','3':'GND','4':'GND'},'Changed PH4 electrical contract')
 ports=json.loads((H/'mechanical/current/power_ports_native.json').read_text(encoding='utf8'))
 for board in ['digital','power']:
  require(ports[board]['pcb_sha256']==summary['boards'][board]['pcb_sha256'],'Stale native power-port extract: '+board)
  require({k:v['net'] for k,v in ports[board]['pads'].items()}==port['pin_map'],'Power cable pin mismatch: '+board)
 require(ports['digital']['xy_mm']==port['position_mm'] and ports['digital']['rotation_deg']==90,'Wrong power port placement')
 require(ports['power']['xy_mm']==[7.5,11.4] and ports['power']['rotation_deg']%360==270,'Wrong side-facing power-strip port')
 side_port=json.loads((H/'mechanical/current/side_power_port_adoption.json').read_text(encoding='utf8'))
 require(side_port['current_pcb_sha256']==summary['boards']['power']['pcb_sha256'] and side_port['P_SW_and_P_FB_geometry_unchanged'],'Stale side-port adoption or boost-core geometry proof')
 require(set(side_port['changed_poses'])=={'JP2','RP4'} and not any(side_port['checks'][k] for k in ['drc','unconnected','schematic_parity']),'Unexpected side-port design scope')
 power_vias=json.loads((H/'mechanical/current/side_power_via_clearance.json').read_text(encoding='utf8'))
 require(power_vias['pcb_sha256']==summary['boards']['power']['pcb_sha256'] and power_vias['selection_source_sha256']==sha(H/'mechanical/current/side_power_port_adoption.json'),'Stale side-power via clearance evidence')
 require(power_vias['minimum_hole_to_smt_copper_mm']==.25 and len(power_vias['new_vias'])==4 and not power_vias['hits'],'Side-power hole/SMD checks failed or incomplete')
 header=ports['digital']['interboard_header']
 require(all(abs(a-b)<.00001 for pin,xy in [('1',[45.7,24.6]),('20',[41.7,17.4])] for a,b in zip(header['pad_centers_mm'][pin],xy)),'Stale SMT interboard projection')
 require(header['mounting']=='SMT_B_NO_F_SIDE_METAL_TAILS' and header['F_side_metal_tail_protrusion_mm']==0,'Interboard connector must be SMT without front metal tails')
 screen_source=json.loads((H/'review/am178_vendor_mechanical_review.json').read_text(encoding='utf8'))
 require(screen_source['status']=='VENDOR_DRAWING_REVIEW_NOT_ASSEMBLY_RELEASE','Re-audit screen source review before changing release status')
 require(sha(ROOT/screen_source['source_pdf'])==screen_source['source_pdf_sha256'],'Changed screen source PDF')
 require(sha(H/'display_link/review/design_contract.json')==screen_source['display_link_contract_sha256'],'Stale screen/FPC target binding')
 require(len(screen_source['selected_native_dimensions'])==8 and screen_source['pdf_page5_visual_observations']['folded_male_solder_plane_to_screen_back_Z_offset_mm'] is None,'Re-audit screen source dimensions before claiming folded Z closure')
 procurement=json.loads((H/'review/smt_btb_procurement_revision_review.json').read_text(encoding='utf8'));require(procurement['status']=='HISTORICAL_JME_VERSION_CONFLICT','Historical JME variants must not become qualified alternates')
 sgd=json.loads((H/'review/sgd_btb_procurement.json').read_text(encoding='utf8'));adoption=H/'review/sgd_btb_adoption.json';sgda=json.loads(adoption.read_text(encoding='utf8'))
 require(sgd['status']=='TAOBAO_PAIR_AND_DRAWING_VERIFIED_ENGINEERING_ADOPTED' and sgd['pcb_adoption_sha256']==sha(adoption),'Stale SGDCONN procurement/adoption chain')
 require(sgd['male']['sku_id']=='5677537797627' and sgd['female']['sku_id']=='5677537797637' and sgd['drawing_dimensions_mm']['mated_height_tolerance'] is None,'SGD option or tolerance scope changed')
 require(set(sgd['files_sha256'])=={'sgd_h40_ph08.jpg','sgd_h45_ph08.jpg'},'SGD evidence must contain only the curated technical screenshots')
 require(sgd['drawing_dimensions_mm']['pad_size']==[.3,2.] and sgd['drawing_dimensions_mm']['locator_hole_span']==9.0 and sgd['drawing_dimensions_mm']['contacts']==20,'Changed SGD drawing geometry')
 for name,digest in sgd['files_sha256'].items():require(sha(H/'review/procurement'/name)==digest,'Changed SGDCONN option screenshot')
 via_sgd=json.loads((H/'review/sgd_btb_current_via_clearance.json').read_text(encoding='utf8'));require(via_sgd['adoption_sha256']==sha(adoption) and via_sgd['minimum_hole_to_smt_copper_mm']==.25,'Stale current SGD via check')
 for name,row in sgda['boards'].items():
  require(row['candidate_pcb_sha256']==summary['boards'][name]['pcb_sha256'] and row['all_other_component_electrical_and_pose_geometry_unchanged'] and row['all20_JH1_pad_centers_and_nets_unchanged'] and row['locator_holes_unchanged'] and not row['hits'],'Stale/dirty SGD migration '+name)
  require(via_sgd['boards'][name]['pcb_sha256']==row['candidate_pcb_sha256'] and not via_sgd['boards'][name]['hits'] and via_sgd['boards'][name]['moved_vias_against_all_SMD_pads']==(4 if name=='afe' else 8),'Incomplete current SGD via check '+name)
  require(smt['boards'][name]['sgd_followup_proof_sha256']==sha(adoption),'Missing historical SMT follow-up chain '+name)
 for f in procurement['native_footprints']:require(sha(H/'footprints/YuEEG.pretty'/(f['footprint']+'.kicad_mod'))==f['sha256'],'Stale BTB drawing/native comparison')
 mating=json.loads((H/'review/interboard_xy_check.json').read_text(encoding='utf8'));require(mating['pins_checked']==20 and mating['mismatches']==0 and mating['electrical_drills']==0,'Missing checked SMT mating contract')
 for board,digest in mating['pcb_sha256'].items():require(digest==summary['boards'][board]['pcb_sha256'],'Stale SMT mapping source '+board)
 for name,digest in mating['footprint_sha256'].items():require(sha(H/'footprints/YuEEG.pretty'/name)==digest,'Changed SMT mating library '+name)
 cable=json.loads((H/'mechanical/current/power_harness_routing_review.json').read_text(encoding='utf8'))
 require(cable['native_ports_sha256']==sha(H/'mechanical/current/power_ports_native.json'),'Stale cable source binding')
 require(cable['native_ports']==ports and cable['status'].endswith('NOT_ASSEMBLY_RELEASE'),'Cable reservation must remain conditional')
 require(cable['display_fpc_pcb_sha256']==sha(H/'display_link/YuEEG_H_DISPLAY_LINK.kicad_pcb'),'Stale cable/FPC binding')
 require(all(w['minimum_signed_gap_mm']>0 for w in cable['current_right_exit_wires']),'Modeled cable overlaps the FPC reservation')
 complete_cable=json.loads((H/'mechanical/current/complete_power_harness_review.json').read_text(encoding='utf8'))
 require(complete_cable['status']=='COMPLETE_NOMINAL_ENDPOINT_ROUTE_NOT_QUALIFIED_HARNESS','Complete route must retain its actual qualification scope')
 complete_sources={'power_ports_native.json':H/'mechanical/current/power_ports_native.json','pogo_assembly_review.json':H/'mechanical/current/pogo_assembly_review.json','interboard_contract.json':H/'review/interboard_contract.json','design_contract.json':H/'display_link/review/design_contract.json'}
 for name,path in complete_sources.items():require(sha(path)==complete_cable['source_sha256'][name],'Stale complete cable input: '+name)
 require(len(complete_cable['wires'])==4 and {w['pin']:w['net'] for w in complete_cable['wires']}==port['pin_map'],'Wrong complete cable pin map')
 require(all(v['tube_gap_lower_bound_mm']>0 for v in complete_cable['wire_pair_clearances']) and len(complete_cable['wire_pair_clearances'])==6,'Missing nominal wire-pair screening')
 require(all(v['wire_tube_gap_lower_bound_mm']>0 for v in complete_cable['obstacles_checked'].values()),'Nominal complete cable overlaps a checked obstacle')
 require(all(v['finite_cylinder_wire_gap_lower_bound_mm']>0 for v in complete_cable['finite_fixing_cylinder_screens']),'Nominal cable overlaps the bounded fixing model')
 require(complete_cable['assumptions']['fixing_head_maximum_projection_above_digital_F_mm']==2.0 and complete_cable['assumptions']['factory_screen_back_Z_qualified'] is False,'Re-audit fixing/screen conditions before changing assembly scope')
 require(not complete_cable['assumptions']['allowed_wire_bend_radius_qualified'] and not complete_cable['assumptions']['terminal_insertion_depths_and_cut_lengths_qualified'],'Re-audit cable supplier evidence before changing qualification')
 hb=header['native_pad_bbox_xy_mm'];require(cable['conditional_JH1_post_envelope_mm']==[hb[0],hb[1],0,hb[2],hb[3],0],'Cable report uses incorrect header geometry')
 screen=json.loads((H/'mechanical/current/afe_host_screen.json').read_text(encoding='utf8'))
 require(screen['afe_pcb_sha256']==summary['boards']['afe']['pcb_sha256'] and screen['digital_pcb_sha256']==summary['boards']['digital']['pcb_sha256'],'Stale AFE/HOST conditional screen')
 require(screen['afe_copper_y_max_mm']<=47.5001 and screen['c405_minimum_external_host_lower_bound_mm']>8,'AFE conditional screen no longer meets its engineering assumptions')
 change=json.loads((H/'afe/review/power_shadow_change.json').read_text(encoding='utf8'))
 require(change['current_pcb_sha256']=={name:summary['boards'][name]['pcb_sha256'] for name in ['afe','digital']},'Stale analog power change record')
 mouth=json.loads((H/'mechanical/current/usb_mouth_review.json').read_text(encoding='utf8'))
 for name in ['afe','digital']:require(mouth['current_pcb_sha256'][name]==summary['boards'][name]['pcb_sha256'],'Stale USB mouth review: '+name)
 tails=json.loads((H/'mechanical/current/power_port_tail_review.json').read_text(encoding='utf8'))
 require(tails['digital_pcb_sha256']==summary['boards']['digital']['pcb_sha256'] and tails['afe_pcb_sha256']==summary['boards']['afe']['pcb_sha256'],'Stale tail/AFE screening')
 require(tails['status']=='CONDITIONAL_TAIL_SCREEN_NOT_ASSEMBLY_RELEASE' and tails['maximum_tail_solder_projection_allowed_below_digital_mm']==1.2,'Missing conditional tail-trim constraint')
 artifacts=json.loads((H/'mechanical/current/power_harness_artifacts.json').read_text(encoding='utf8'))
 require(all(name in artifacts['files_sha256'] for name in ['complete_power_harness_review.json','complete_power_harness_review.png','complete_power_harness_review.svg']),'Complete cable artifacts not bound')
 for name,digest in artifacts['files_sha256'].items():require(sha(H/'mechanical/current'/name)==digest,'Changed cable-review artifact: '+name)
 for name,digest in artifacts['pcb_sha256'].items():require(digest==summary['boards'][name]['pcb_sha256'],'Stale cable-review PCB binding: '+name)
 env=json.loads((H/'review/component_envelopes.json').read_text(encoding='utf8'))
 for model in env['models']:require(sha(H/'models'/model['model'])==model['sha256'],'Changed dimensional model: '+model['model'])
 require(info['protocol_tests_passed']==6 and info['physical_flash_or_transport_tested'] is False,'Unexpected test scope')
 power=H/'power';pbom=list(csv.DictReader((power/'BOM.csv').open(encoding='utf-8-sig')));prow=next(v for v in pbom if v['Reference']=='JP1')
 require(prow['Quantity']=='2' and sum(int(v['Quantity']) for v in pbom)==22,'Pogo pair BOM quantities must represent two physical probes')
 pt=loads((power/'YuEEG_H_POWER.kicad_pcb').read_text(encoding='utf8'));require(float(sub(sub(pt,'general'),'thickness')[1])==1.0,'Pogo board must be nominal 1mm')
 stack=sub(sub(pt,'setup'),'stackup');require(abs(sum(float(sub(v,'thickness')[1]) for v in stack if isinstance(v,list) and v[0]=='layer')-1)<1e-8,'Power stackup and general thickness differ')
 pogo=json.loads((H/'mechanical/current/pogo_assembly_review.json').read_text(encoding='utf8'));require(pogo['power_pcb_sha256']==summary['boards']['power']['pcb_sha256'],'Stale pogo assembly evidence')
 require(all(v['error_mm']<1e-6 and v['drill_mm']==.7 for v in pogo['rows']),'Pogo nominal alignment or drill changed')
 hole_adopt=H/'mechanical/current/pogo_hole_tolerance_adoption.json';ha=json.loads(hole_adopt.read_text(encoding='utf8'));fit=json.loads((H/'mechanical/current/pogo_hole_fit_review.json').read_text(encoding='utf8'))
 require(ha['current_pcb_sha256']==summary['boards']['power']['pcb_sha256'] and ha['all_tracks_vias_unchanged'] and ha['all_other_footprints_unchanged'] and ha['JP1_only_description_and_drill_changed'] and not ha['same_net_smt_hole_hits'],'Dirty/stale pogo drill migration')
 require(side_port['pogo_hole_followup_proof_sha256']==sha(hole_adopt) and fit['adoption_sha256']==sha(hole_adopt),'Missing side-port/pogo follow-up chain')
 require(fit['pcb_sha256']==summary['boards']['power']['pcb_sha256'] and fit['source_fact_sha256']==sha(H/'mechanical/current/pogo_source_and_hole_review.json') and fit['probe_reference_sha256']==sha(H/'mechanical/current/pogo_reference.json'),'Stale pogo diameter-process evidence')
 require(fit['footprint_library_sha256']==sha(H/'footprints/YuEEG.pretty/NPBX1_MillMax0906_Dplus_Bminus_10mm.kicad_mod'),'Stale probe hole library evidence')
 require(len(fit['rows'])==2 and all(v['margin_over_part_recommendation_mm']>0 for v in fit['rows']) and not fit['hits'],'Pogo hole process or SMT clearance failed')
 require(pogo['terminal_confirmation_file_sha256']==sha(H/'mechanical/current/npbx1_user_terminal_order.json'),'Changed user terminal confirmation')
 selected=json.loads((H/'digital/review/r1101_height_selection.json').read_text(encoding='utf8'))
 require(selected.get('current_pcb_sha256',selected['after_pcb_sha256'])==summary['boards']['digital']['pcb_sha256'],'Stale R1101 height selection record')
 require(selected['mpn']=='RC0402FR-0722RL' and selected['body_max_mm']==[1.05,.55,.4] and selected['maximum_mounted_height_for_fold_screen_mm']==.5,'Changed R1101 selected height contract')
 imu=json.loads((H/'digital/review/merge_contract.json').read_text(encoding='utf8'));require(imu['pcb_sha256']==summary['boards']['digital']['pcb_sha256'] and imu['parts']==129 and imu['adopted_main_development'],'Stale IMU main-board binding')
 require(sha(H/'models/Murata_SCH16T_SOIC24_nominal.wrl')==imu['nominal_model_sha256'],'Changed IMU nominal illustration')
 stackimu=json.loads((H/'mechanical/current/imu_interboard_review.json').read_text(encoding='utf8'));require(stackimu['digital_pcb_sha256']==imu['pcb_sha256'] and stackimu['afe_pcb_sha256']==summary['boards']['afe']['pcb_sha256'],'Stale IMU interboard screening')
 require(stackimu['required_minimum_local_gap_mm']==8.3 and len(stackimu['rows'])==16,'Missing IMU assembly height constraint')
 require(info['navigation_implemented'] is True and info['imu_continuous_sampling_implemented'] is True and info['navigation_scope']=='RELATIVE_ATTITUDE_3S_UNREFERENCED_NO_UWB','Unexpected relative-motion implementation scope')
 require(info['trajectory_window_seconds']==3 and info['imu_hardware_tested'] is False,'Relative motion must retain engineering horizon and hardware-test scope')
 require(info['motion_protocol_tests_passed']==10 and info['relative_motion_checks_passed']==36,'Missing motion validation')
 for name,digest in info['tools_source_sha256'].items():require(sha(H/'firmware/tools'/name)==digest and sha(ROOT/'Firmware/tools'/name)==digest,'Changed checked motion/EEG tool '+name)
 for name,digest in info['motion_tests_sha256'].items():require(sha(H/'firmware/build'/name)==digest,'Changed motion test evidence '+name)
 motion_contract=json.loads((H/'review/firmware_motion_contract.json').read_text(encoding='utf8'));require(motion_contract['status']=='PASS' and motion_contract['firmware_spi3_source_sha256']==info['source_sha256']['YuEEG_SPI3.h'],'Changed checked IMU GPIO constants')
 require(motion_contract['exported_netlist_sha256']==sha(H/'digital/review/netlist.xml') and len(motion_contract['pins'])==8,'Stale IMU/display native GPIO evidence')
 authority=json.loads((H/'review/publication_authorization.json').read_text(encoding='utf8'));require(authority['derived_model_publication']['authorized'] is True and authority['navigation_choice']['uwb_anchors'] is False,'User publication/navigation decisions differ')
 underbody=json.loads((H/'digital/review/imu_underbody_rule_check.json').read_text(encoding='utf8'));require(underbody['pcb_sha256']==imu['pcb_sha256'] and underbody['rule_attached_to']=='U1801','Stale IMU footprint no-pour rule check')
 require(sha(H/'footprints/YuEEG_IMU.pretty/Murata_SCH16T_SOIC24_14p20x9p30_P0p80.kicad_mod')==underbody['footprint_library_sha256'],'Changed IMU no-pour footprint library')
 require(len(underbody['layers'])==6 and all(q['pour_covered_samples']==0 for q in underbody['layers']),'Unexpected pour below IMU')
 refimu=json.loads((H/'digital/review/imu_underbody_pour_review.json').read_text(encoding='utf8'));require(refimu['trial_pcb_sha256']==smt['boards']['digital']['baseline_pcb_sha256'],'Changed historical pre-SMT IMU reference comparison')
 require(all(refimu['nets'][n]['newly_missing_any_reference']==0 for n in ['ADS_CS','ADS_SCLK','ADS_MOSI','ADS_MISO']),'Changed EEG SPI reference coverage')
 require(all(q['newly_missing_any_reference']==0 for n,q in refimu['nets'].items() if n.startswith('USB_')),'Changed USB reference coverage')
 viamu=json.loads((H/'digital/review/new_ground_via_smd_clearance.json').read_text(encoding='utf8'));require(viamu['after_pcb_sha256']==smt['boards']['digital']['baseline_pcb_sha256'] and all(not q['near_smd_pad_hits_at_0p25_clearance'] for q in viamu['new_vias']),'New IMU ground via overlaps SMT pad clearance')
 current_vias=json.loads((H/'digital/review/imu_ground_via_current_clearance.json').read_text(encoding='utf8'));require(current_vias['pcb_sha256']==imu['pcb_sha256'] and current_vias['historical_via_selection_sha256']==sha(H/'digital/review/new_ground_via_smd_clearance.json') and len(current_vias['vias'])==3 and all(not v['hits'] for v in current_vias['vias']),'Stale/dirty current IMU via check')
 groundimu=json.loads((H/'digital/review/imu_ground_fill_paths.json').read_text(encoding='utf8'));require(groundimu['source_sha256']==imu['pcb_sha256'],'Stale IMU ground-return screen')
 exports=json.loads((H/'fabrication_engineering/MANIFEST.json').read_text(encoding='utf8'));require(exports['status']=='ENGINEERING_REVIEW_ONLY_NOT_FOR_ORDER','Export status is not an engineering draft')
 for q in exports['boards']:
  require(q['pcb_sha256']==summary['boards'][q['board']]['pcb_sha256'],'Stale Gerber export '+q['board'])
  for name,digest in q['files'].items():require(sha(H/'fabrication_engineering'/q['board']/name)==digest,'Changed engineering export '+name)
 drill=(H/'fabrication_engineering/digital/YuEEG_H_DIGITAL-PTH.drl').read_text(encoding='utf8');tools={};active=None;holes=[]
 require('METRIC' in drill,'Unexpected drill units')
 for line in drill.splitlines():
  definition=re.fullmatch(r'T(\d+)C([\d.]+)',line);selection=re.fullmatch(r'T(\d+)',line);point=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
  if definition:tools[definition[1]]=float(definition[2])
  elif selection:active=selection[1]
  elif point and tools.get(active)==.75:holes.append((float(point[1]),float(point[2])))
 require(sorted(holes)==sorted((v['xy_mm'][0],-v['xy_mm'][1]) for v in ports['digital']['pads'].values()),'PH4 0.75mm plated drill export mismatch')
 power_drill=(H/'fabrication_engineering/power/YuEEG_H_POWER-PTH.drl').read_text(encoding='utf8');power_tools={};power_active=None;power_probe_holes=[]
 require('METRIC' in power_drill,'Unexpected probe drill units')
 for line in power_drill.splitlines():
  definition=re.fullmatch(r'T(\d+)C([\d.]+)',line);selection=re.fullmatch(r'T(\d+)',line);point=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
  if definition:power_tools[definition[1]]=float(definition[2])
  elif selection:power_active=selection[1]
  elif point and power_tools.get(power_active)==.7:power_probe_holes.append((float(point[1]),float(point[2])))
 require(sorted(power_probe_holes)==[(18.9,-1.5),(28.9,-1.5)],'JP1 0.70mm plated drill export mismatch')
 with (H/'fabrication_engineering/digital/placement_front.csv').open(encoding='utf8',newline='') as stream:require(all(r['Ref']!='JH2' for r in csv.DictReader(stream)),'TH PH4 must not be listed as an SMT placement')
 if (H/'display_link').exists():
  from verify_display_link import verify as verify_fpc
  verify_fpc()
 print('PASS: Rev H engineering checkpoint: native pin/BOM/source hashes, zero static reports, firmware and review exports. Mechanical/functional release remains incomplete.')
if __name__=='__main__':verify()

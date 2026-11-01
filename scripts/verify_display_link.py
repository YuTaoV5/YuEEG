"""Check published passive-FPC prototype bindings; no manufacturing release."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'hardware/YuEEG_8CH_RevH_Stack';D=H/'display_link'
def verify():
 q=json.loads((D/'review/checkpoint.json').read_text());assert q['status']=='PROTOTYPE_NOT_FOR_ORDER'
 sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
 for name,digest in q['source_files_sha256'].items():assert sha(D/name)==digest,'Stale FPC source/report: '+name
 for name,digest in q['baseline_pcb_sha256'].items():assert sha(H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb'))==digest,'Changed FPC baseline: '+name
 drc=json.loads((D/'review/drc_current.json').read_text());erc=json.loads((D/'review/erc_current.json').read_text());fold=json.loads((D/'review/fold_alignment.json').read_text())
 assert all(not drc[k] for k in ['violations','unconnected_items','schematic_parity']) and not any(s['violations'] for s in erc['sheets'])
 assert fold['pcb_sha256']==sha(D/'YuEEG_H_DISPLAY_LINK.kicad_pcb') and not fold['bend_vias'] and not fold['nonparallel_tracks_in_bend']
 assert all(v['error_mm']<1e-5 for v in fold['upper_socket_folded_pad_checks'])
 space=json.loads((D/'review/fold_space.json').read_text());assert space['status']=='CONDITIONAL_NOMINAL_SPACE_SCREEN_NOT_ASSEMBLY_RELEASE'
 assert space['fpc_pcb_sha256']==sha(D/'YuEEG_H_DISPLAY_LINK.kicad_pcb') and space['digital_pcb_sha256']==q['baseline_pcb_sha256']['digital']
 assert space['design_contract_sha256']==sha(D/'review/design_contract.json') and space['neighbor_native_sha256']==sha(D/'review/neighbor_native.json')
 assert space['sweep_checker_sha256']==sha(H/'review/devtools/check_h_display_fold_space.py') and space['native_fab_geometry_sha256']==sha(D/'review/fab_geometry.json'),'Stale native outline/fold-model binding'
 fab=json.loads((D/'review/fab_geometry.json').read_text());adopt=json.loads((D/'review/fab_geometry_adoption.json').read_text())
 assert fab['pcb_sha256']==sha(D/'YuEEG_H_DISPLAY_LINK.kicad_pcb')==adopt['current_pcb_sha256'] and fab['contract_sha256']==sha(D/'review/design_contract.json')
 assert fab['project_sha256']==sha(D/'YuEEG_H_DISPLAY_LINK.kicad_pro') and fab['rules_sha256']==sha(D/'YuEEG_H_DISPLAY_LINK.kicad_dru')
 assert fab['checker_sha256']==sha(H/'review/devtools/check_h_fpc_fab_geometry.py') and adopt['adoption_script_sha256']==sha(H/'review/devtools/adopt_h_fpc_fab_geometry.py')
 assert fab['minimum_pad_edge_gap_mm']>=.3 and fab['minimum_track_via_edge_gap_mm']>=.3 and len(fab['all56_rectangular_SMD_pads'])==56
 assert fab['minimum_copper_edge_constraint_mm']==.3 and fab['minimum_exposed_pad_other_net_copper_constraint_mm']==.15
 assert len(fab['F_PI_stiffener_regions'])==2 and all(r['filled'] and r['stroke_width_mm']==0 for r in fab['F_PI_stiffener_regions'])
 assert fab['native_per_layer_stack_approved'] is False and fab['native_numeric_per_layer_stack_present'] is False,'Re-audit accepted laminate before asserting a production stack'
 assert adopt['all_56_pad_geometry_nets_and_both_connector_poses_unchanged'] and len(adopt['only_GND_four_track_endpoint_adjustments'])==4 and adopt['all_vias_unchanged']
 assert all(v['minimum_nominal_box_distance_mm']>0 for v in space['neighbors']), 'Potential intersection of selected FPC envelope boxes'
 selected=json.loads((H/'digital/review/r1101_height_selection.json').read_text());r=next(v for v in space['neighbors'] if v['ref']=='R1101_selected_low_profile')
 assert r['box'][5]==selected['maximum_mounted_height_for_fold_screen_mm'] and r['source']==selected['source'],'FPC resistor height must match selected BOM MPN'
 print('PASS: display FPC prototype source/report bindings, zero static reports and fold geometry. Physical mating and fabrication remain unqualified.')
if __name__=='__main__':verify()

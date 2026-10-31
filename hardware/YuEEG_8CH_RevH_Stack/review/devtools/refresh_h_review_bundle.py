"""Refresh current read-only evidence; never rebuild or place source boards."""
from pathlib import Path
import subprocess,sys,json,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');native='X:/SoftWare/Kicad/bin/python.exe';default=sys.executable
jobs=[(native,n) for n in ['rebind_h_graphic_evidence','capture_h_current_placement','audit_h_models','audit_h_usb_geometry','audit_h_usb_reference','audit_h_decoupler_ground','check_h_mating_geometry','check_h_screen_envelope','check_h_battery_side_envelope','extract_h_power_ports','check_h_power_port_tails','extract_h_host_external','audit_h_display_link_fold','inspect_h_fpc_neighbors']]
jobs += [(default,n) for n in ['review_h_right_power_harness','plot_h_right_power_harness','plot_h_battery_side_envelope','check_h_display_fold_space','plot_h_display_fold_space']]
jobs += [(native,'checkpoint_h_display_link')]
for exe,name in jobs:
 script=Path('logs')/(name+'.py');assert script.exists(),script
 with (Path('logs')/(name+'_refresh.log')).open('w',encoding='utf8') as out:subprocess.run([exe,str(script)],stdout=out,stderr=subprocess.STDOUT,check=True)
 print('PASS',name,flush=True)
for file in [H/'mechanical/current/usb_mouth_review.json',H/'afe/review/power_shadow_change.json']:
 data=json.loads(file.read_text());data['current_pcb_sha256']={name:hashlib.sha256((H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb')).read_bytes()).hexdigest() for name in ['afe','digital']};file.write_text(json.dumps(data,indent=2),encoding='utf8')
# The right-port placement is unchanged: native extract verifies its contract.
rp=H/'digital/review/right_power_port.json';port=json.loads(rp.read_text());ports=json.loads((H/'mechanical/current/power_ports_native.json').read_text());assert ports['digital']['xy_mm']==port['position_mm'] and ports['digital']['rotation_deg']==port['rotation_deg'];assert {k:v['net'] for k,v in ports['digital']['pads'].items()}==port['pin_map'];port['after_pcb_sha256']=ports['digital']['pcb_sha256'];rp.write_text(json.dumps(port,indent=2),encoding='utf8')
print('Bundle refreshed; source reports, exports, rendering and final verifier still required')

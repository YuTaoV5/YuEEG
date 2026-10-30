"""Derive a possible USB-to-power-strip partition from the current native net graph.

This is an architecture feasibility report, not an implemented board revision.
"""
from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('hardware/YuEEG_8CH_RevH_Stack');path=R/'digital/YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));pro=json.loads(path.with_suffix('.kicad_pro').read_text());host={r['pattern'] for r in pro['net_settings']['netclass_patterns'] if r['netclass']=='USB_HOST'};parts={f.GetReference():f for f in b.GetFootprints()};pn={r:{q.GetNetname() for q in f.Pads() if q.GetNetname()} for r,f in parts.items()}
move={r for r,ns in pn.items() if ns&host}
assert pn['C703']=={'+3V3','GND'}
move.add('C703') # Native local acquisition-side U701 decoupler; shared rail alone cannot identify it.
# Include the isolator's local acquisition-side bias/decoupling parts, not MCU series resistors.
for r,ns in pn.items():
 if r.startswith(('C','R')) and ns and ns<={'USB_VDD2','USB_ISO_PD','USB_ISO_SPEED','+3V3','GND'} and ns&{'USB_VDD2','USB_ISO_PD','USB_ISO_SPEED'}:move.add(r)
outside={net for r,ns in pn.items() if r not in move for net in ns};inside={net for r in move for net in pn[r]};cross=sorted(inside&outside);records=[]
for r in sorted(move):
 f=parts[r];records.append({'reference':r,'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibItemName()),'nets':sorted(pn[r])})
report={'status':'PARTITION_FEASIBILITY_ONLY_NOT_IMPLEMENTED','source_pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'proposed_move_components':records,'component_count':len(records),'boundary_nets':cross,'remaining_digital_component_count':113-len(move),'existing_power_outline_mm':[34,18],'existing_stack_outline_mm':[48,60],'screen_projection_mm':[34.14,42.74],'constraints':['Power strip must preserve the same 8 mm host/device copper separation, including battery probes, cable pins, mounting hardware and all layers.','The existing 34 x 18 mm strip cannot be assumed to fit the added isolation circuit. No new board size or probe position is selected.','A new cable must preserve protected-cell telemetry and power and add isolated-side USB D+/D-, reference ground and any necessary supply connections.','Both stack boards must be re-placed and re-routed; moving USB alone does not prove screen-sized boards or display FPC reach.','Main native boards, pin contracts and engineering exports are unchanged by this report.']}
(R/'mechanical/current/usb_partition_feasibility.json').write_text(json.dumps(report,indent=2));print('move',len(records),'parts');print([(r['reference'],r['value'],r['nets']) for r in records]);print('boundary nets',cross)

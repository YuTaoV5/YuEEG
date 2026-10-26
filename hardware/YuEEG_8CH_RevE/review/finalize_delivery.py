"""Validate final reports against the exact PCB, assemble firmware and zip review files."""
from pathlib import Path
import pcbnew as p,json,csv,collections,hashlib,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1];workspace=ROOT.parents[1];path=ROOT/'YuEEG_8CH_RevE.kicad_pcb';digest=hashlib.sha256(path.read_bytes()).hexdigest()
b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
drc=json.loads((ROOT/'review/pcb_drc.json').read_text(encoding='utf8'));assert all(not drc[k] for k in ['violations','unconnected_items','schematic_parity'])
assert '0 个错误 0 个警告' in (ROOT/'review/ERC.rpt').read_text(encoding='utf8')
for name in ['ELECTRICAL_AUDIT.json','REV_E_ELECTRICAL_AUDIT.json']:assert json.loads((ROOT/'review'/name).read_text())['sha256_pcb']==digest
assert len(fps)==378
edgepts=[v for d in b.GetDrawings() if d.GetLayer()==p.Edge_Cuts and isinstance(d,p.PCB_SHAPE) for v in [d.GetStart(),d.GetEnd()]]
envelope=[round(p.ToMM(max(q.x for q in edgepts)-min(q.x for q in edgepts)),3),round(p.ToMM(max(q.y for q in edgepts)-min(q.y for q in edgepts)),3)];assert envelope==[94,122],envelope
segments=collections.Counter();vias=[];vip=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  vias.append(t)
  touched=[f'{f.GetReference()}.{q.GetNumber()}' for f in fps.values() for q in f.Pads() if q.GetNetCode()==t.GetNetCode() and not q.GetDrillSize().x and q.GetEffectiveShape(q.GetLayer()).Collide(p.SHAPE_CIRCLE(t.GetPosition(),int(t.GetDrillValue()/2)),0)]
  if touched:vip.append({'x_mm_absolute':p.ToMM(t.GetPosition().x),'y_mm_absolute':p.ToMM(t.GetPosition().y),'pads':touched,'diameter_mm':p.ToMM(t.GetWidth(p.F_Cu)),'drill_mm':p.ToMM(t.GetDrillValue())})
 else:segments[b.GetLayerName(t.GetLayer())]+=1
assert 'In1.Cu' not in segments
(ROOT/'review/via_in_pad.json').write_text(json.dumps(vip,indent=2))
report={'revision':'E','date':'2026-10-27','pcb_envelope_mm':envelope,'copper_layers':4,'footprints':len(fps),'top_footprints':sum(f.GetLayer()==p.F_Cu for f in fps.values()),'bottom_footprints':sum(f.GetLayer()==p.B_Cu for f in fps.values()),'schematic_sheets':15,'ERC_violations':0,'DRC_violations':0,'unconnected_items':0,'schematic_parity_issues':0,'all_exported_ref_pin_pairs_checked':1068,'track_segments_by_layer':dict(segments),'vias':len(vias),'via_in_pad_require_filled_capped':len(vip),'default_clearance_mm':.15,'NexFET_pad_local_clearance_mm':.13,'minimum_board_clearance_mm':.13,'minimum_via_diameter_mm':.5,'minimum_drill_mm':.2,'host_system_clearance_rule_mm':8,'sha256_pcb':digest,'firmware_build_fqbn':'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB','firmware_flash_tested':False,'release_scope':'Engineering review only. Physical USB, battery, noise, thermal, EMC and patient-safety qualification pending.'}
(ROOT/'review/PCB_validation.json').write_text(json.dumps(report,indent=2))
with (ROOT/'BOM_with_placement.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Side','X_mm_from_left','Y_mm_from_top','Rotation_deg'])
 for r,q in sorted(fps.items()):w.writerow([r,q.GetValue(),q.GetFPIDAsString(),'TOP' if q.GetLayer()==p.F_Cu else 'BOTTOM',round(p.ToMM(q.GetPosition().x)-70,4),round(p.ToMM(q.GetPosition().y)-100,4),q.GetOrientationDegrees()])
(ROOT/'review/placement_report.json').write_text(json.dumps({'origin_absolute_mm':[70,100],'parts':{r:{'x_mm':round(p.ToMM(f.GetPosition().x)-70,4),'y_mm':round(p.ToMM(f.GetPosition().y)-100,4),'side':'TOP' if f.GetLayer()==p.F_Cu else 'BOTTOM','rotation_deg':f.GetOrientationDegrees()} for r,f in fps.items()}},indent=2))
for subdir in ['ads1299_driver','tools','build']: (ROOT/'firmware'/subdir).mkdir(parents=True,exist_ok=True)
for name in ['ads1299_driver.ino','YuEEG.h','YuEEG_UI.h','README.md']:shutil.copy2(workspace/'Firmware/ads1299_driver'/name,ROOT/'firmware/ads1299_driver'/name)
for name in ['receive_eeg.py','test_protocol.py','send_eeg_command.py']:shutil.copy2(workspace/'Firmware/tools'/name,ROOT/'firmware/tools'/name)
for q in (workspace/'Firmware/build_revE').glob('*.bin'):shutil.copy2(q,ROOT/'firmware/build'/q.name)
shutil.copy2(workspace/'Firmware/build_revE.log',ROOT/'firmware/build/build.log')
source=workspace/'Firmware/ads1299_driver/YuEEG.h';compiled=(workspace/'Firmware/build_revE/sketch/YuEEG.h').read_text()
if compiled.startswith('#line '):compiled=compiled.split('\n',1)[1]
assert compiled==source.read_text(),'Compiled header does not match delivered source'
ui_source=workspace/'Firmware/ads1299_driver/YuEEG_UI.h';ui_compiled=(workspace/'Firmware/build_revE/sketch/YuEEG_UI.h').read_text()
if ui_compiled.startswith('#line '):ui_compiled=ui_compiled.split('\n',1)[1]
assert ui_compiled==ui_source.read_text(),'Compiled UI header does not match delivered source'
(ROOT/'firmware/build/BUILD_INFO.json').write_text(json.dumps({'fqbn':report['firmware_build_fqbn'],'arduino_esp32_core':'2.0.11','source_header_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'ui_header_sha256':hashlib.sha256((workspace/'Firmware/ads1299_driver/YuEEG_UI.h').read_bytes()).hexdigest(),'binaries_sha256':{q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in (ROOT/'firmware/build').glob('*.bin')},'protocol_tests_passed':6,'physical_flash_or_transport_tested':False,'notes':'Binary components accompany the source build. Use the documented Arduino IDE/CLI workflow to flash; no merged full-flash image is supplied.'},indent=2))
(ROOT/'fabrication_review/ASSEMBLY_NOTES.md').write_text(f'''# Rev E fabrication review notes

Engineering review only; obtain a board-house process review before ordering.

- Four copper layers; 94 x 122 mm; nominal 1.6 mm board. Confirm stack-up and USB trace impedance with the fabricator.
- Standard trace / clearance: 0.15 mm; local NexFET pad clearance: 0.13 mm. Minimum via: 0.5 mm copper / 0.2 mm drill.
- **{len(vip)} vias intersect SMT pads. These require filled and copper-capped via-in-pad processing, not an ordinary open/tented hole.** Coordinates and associated pads: `../review/via_in_pad.json`, absolute KiCad millimetres. Review paste and assembly before fabrication.
- HOST and system copper are separated by an 8 mm rule on all layers. Preserve the L-shaped no-copper areas; do not bridge with mounting metal, shields or cables.
- THM6-0511 is the standard pin variant, not -B1 or WI. Check manufacturer top/bottom view, height and body against the custom footprint.
- The custom ADuM4160 BRIZ land pattern retains an 8.5 mm copper gap. Verify lead-to-land contact and assembly tolerance against the actual RI-16 package.
- Panasonic EVPBB2A9B000 uses the custom 0.53 mm switch footprint. Review actuator stroke/load.
- DWO DO0200PFS12 must be the RM67162 QSPI variant. Add four M2 insulated 6 mm standoffs, nonconductive fasteners and a verified 18-way module harness. CN1 pitch alone does not guarantee mating. See ASSEMBLY_EXTRAS.csv and REV_E_REVIEW.md.
- The 3D illustration includes original envelope models and does not prove fit or insulation. The screen graphic is a preview.
- Component certifications do not certify this assembled board. USB, battery, thermal, noise, ESD, leakage and dielectric tests remain pending.
''',encoding='utf8')
patterns=['*.kicad_pro','*.kicad_sch','*.kicad_pcb','*.kicad_sym','*.kicad_dru','*.csv','*.pdf','*.md','fp-lib-table','sym-lib-table','libraries/*.kicad_sym','footprints/*/*.kicad_mod','fabrication_review/*','firmware/**/*','review/PCB_3D*.png','review/PCB_top.svg','review/PCB_bottom.svg','review/schematic_contact_sheet.png','review/pcb_drc.json','review/ERC.rpt','review/PCB_validation.json','review/ELECTRICAL_AUDIT.json','review/REV_E_ELECTRICAL_AUDIT.json','review/connectivity_report.json','review/placement_report.json','review/via_in_pad.json','review/netlist.xml','review/expected_connections.json','review/audit_afe.py','review/audit_revision_e.py','review/verify_netlist.py','review/sexpr_io.py','review/host_domain_nets.json','models/*','review/finalize_delivery.py']
files=sorted({q for pattern in patterns for q in ROOT.glob(pattern) if q.is_file()})
manifest={str(q.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(q.read_bytes()).hexdigest() for q in files}
(ROOT/'CHECKSUMS.json').write_text(json.dumps(manifest,indent=2));files.append(ROOT/'CHECKSUMS.json')
out=ROOT.parent/'YuEEG_8CH_RevE_94x122_dual_USB_AMOLED_SD_review.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for q in files:z.write(q,Path(ROOT.name)/q.relative_to(ROOT))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps(report,indent=2));print('Packaged',len(files),'files;',out.stat().st_size,'bytes;',out)

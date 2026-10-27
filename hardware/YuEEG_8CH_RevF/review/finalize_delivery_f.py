"""Bind clean native reports and two-board exports to a curated Rev F archive."""
from pathlib import Path
import pcbnew as p,json,csv,collections,hashlib,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1];workspace=ROOT.parents[1]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
validations=[]
for folder,stem,count,size,pairs,sheets in [(ROOT,'YuEEG_8CH_RevF',305,[70,80],876,16),(ROOT/'isolated_power','YuEEG_8CH_RevF_POWER',50,[44,48],160,4)]:
 path=folder/(stem+'.kicad_pcb');b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
 drc=json.loads((folder/'review/pcb_drc.json').read_text(encoding='utf8'))
 assert all(not drc[k] for k in ['violations','unconnected_items','schematic_parity'])
 assert '0 个错误 0 个警告' in (folder/'review/ERC.rpt').read_text(encoding='utf8')
 assert len(fps)==count and all(f.GetLayer()==p.F_Cu for f in fps.values())
 pts=[v for g in b.GetDrawings() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.Edge_Cuts for v in [g.GetStart(),g.GetEnd()]]
 envelope=[round(p.ToMM(max(v.x for v in pts)-min(v.x for v in pts)),2),round(p.ToMM(max(v.y for v in pts)-min(v.y for v in pts)),2)]
 assert envelope==size,envelope
 segments=collections.Counter();vias=[];vip=[]
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   vias.append(t)
   touched=[f'{f.GetReference()}.{q.GetNumber()}' for f in fps.values() for q in f.Pads() if q.GetNetCode()==t.GetNetCode() and not q.GetDrillSize().x and q.GetEffectiveShape(q.GetLayer()).Collide(p.SHAPE_CIRCLE(t.GetPosition(),int(t.GetDrillValue()/2)),0)]
   if touched:vip.append({'x_mm_absolute':p.ToMM(t.GetPosition().x),'y_mm_absolute':p.ToMM(t.GetPosition().y),'pads':touched,'diameter_mm':p.ToMM(t.GetWidth(p.F_Cu)),'drill_mm':p.ToMM(t.GetDrillValue())})
  else:segments[b.GetLayerName(t.GetLayer())]+=1
 assert 'In1.Cu' not in segments
 (folder/'review/via_in_pad.json').write_text(json.dumps(vip,indent=2))
 report={'revision':'F','date':'2026-10-28','pcb_envelope_mm':envelope,'copper_layers':4,'footprints':count,'top_footprints':count,'bottom_footprints':0,'schematic_sheets':sheets,'ERC_violations':0,'DRC_violations':0,'unconnected_items':0,'schematic_parity_issues':0,'all_exported_ref_pin_pairs_checked':pairs,'track_segments_by_layer':dict(segments),'vias':len(vias),'via_in_pad_require_filled_capped':len(vip),'default_clearance_mm':.15,'local_NexFET_clearance_mm':.13,'minimum_via_diameter_mm':.4,'minimum_drill_mm':.2,'host_system_clearance_rule_mm':8,'sha256_pcb':sha(path),'physical_qualification_completed':False,'scope':'Engineering review only; board-house assembly review and hardware qualification pending.'}
 (folder/'review/PCB_validation.json').write_text(json.dumps(report,indent=2));validations.append(report)
 with (folder/'BOM_with_placement.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Side','X_mm_from_left','Y_mm_from_top','Rotation_deg'])
  for r,q in sorted(fps.items()):w.writerow([r,q.GetValue(),q.GetFPIDAsString(),'TOP',round(p.ToMM(q.GetPosition().x)-80,4),round(p.ToMM(q.GetPosition().y)-100,4),q.GetOrientationDegrees()])
 (folder/'review/placement_report.json').write_text(json.dumps({'origin_absolute_mm':[80,100],'parts':{r:{'x_mm':round(p.ToMM(f.GetPosition().x)-80,4),'y_mm':round(p.ToMM(f.GetPosition().y)-100,4),'side':'TOP','rotation_deg':f.GetOrientationDegrees()} for r,f in fps.items()}},indent=2))
 for subdir in ['fabrication_review']:(folder/subdir).mkdir(exist_ok=True)
 (folder/'fabrication_review/ASSEMBLY_NOTES.md').write_text(f'''# Rev F fabrication and assembly review

PCB {size[0]} × {size[1]} mm; four copper layers; nominal 1.6 mm. All {count} footprints are on the top face. Bottom has no SMT placement. Through-hole headers, USB shell retention and the THM6 module still require a separate solder operation where present.

Default trace/clearance 0.15 mm; local NexFET pad clearance 0.13 mm. Minimum via 0.4 mm copper / 0.2 mm drill. Confirm the proposed stack-up, USB impedance and solder-mask registration with the fabricator.

**{len(vip)} vias intersect SMT pads. Review filled and copper-capped via-in-pad processing.** Coordinates: `../review/via_in_pad.json`. Tenting is not a substitute for filling/capping these holes. Use this inventory for a board-house quotation before ordering.

The dedicated Samtec FTSH-110 custom footprint follows manufacturer Rev H land dimensions; its suggested 0.152 mm stencil must be reconciled with 0402 parts using a reviewed stencil/profile. Module envelope models are illustrative. Confirm pin 1, connector mating, paste apertures and all actual component heights.

Preserve the 8 mm host/secondary copper barrier on every layer and the no-copper moat. Nonconductive mounting hardware must not bridge it. Main J301 pogo is nonisolated bench access. Unplug the entire electrode harness before charging or using nonisolated debug equipment.

AMOLED uses four nominal 8 mm insulated standoffs and a verified custom 20-to-18 harness. Confirm supplier CN1, actual mating height, cable bend radius, antenna clearance and enclosure access. Battery and enclosure are not selected; PCB dimensions do not specify the complete device volume.

Engineering review only. Actual rails, startup, USB/Wi-Fi/SD concurrency, noise, thermal behavior, pack protection, charging, leakage and dielectric performance require bench qualification before electrode use.
''',encoding='utf8')
for n in ['ELECTRICAL_AUDIT.json','REV_F_ELECTRICAL_AUDIT.json']:
 audit=json.loads((ROOT/'review'/n).read_text());assert audit['sha256_pcb']==validations[0]['sha256_pcb']
assert audit['sha256_power_pcb']==validations[1]['sha256_pcb']
for subdir in ['ads1299_driver','tools','build']:(ROOT/'firmware'/subdir).mkdir(parents=True,exist_ok=True)
for name in ['ads1299_driver.ino','YuEEG.h','YuEEG_UI.h','README.md']:shutil.copy2(workspace/'Firmware/ads1299_driver'/name,ROOT/'firmware/ads1299_driver'/name)
for name in ['receive_eeg.py','test_protocol.py','send_eeg_command.py']:shutil.copy2(workspace/'Firmware/tools'/name,ROOT/'firmware/tools'/name)
for f in (workspace/'Firmware/build_revF').glob('*.bin'):shutil.copy2(f,ROOT/'firmware/build'/f.name)
shutil.copy2(workspace/'Firmware/build_revF.log',ROOT/'firmware/build/build.log')
for name in ['YuEEG.h','YuEEG_UI.h']:
 compiled=workspace/'Firmware/build_revF/sketch'/name;lines=compiled.read_text().splitlines()
 assert lines[0].startswith('#line 1 ')
 assert lines[1:]==(workspace/'Firmware/ads1299_driver'/name).read_text().splitlines()
info={'fqbn':'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB','arduino_esp32_core':'2.0.11','source_header_sha256':sha(workspace/'Firmware/ads1299_driver/YuEEG.h'),'ui_header_sha256':sha(workspace/'Firmware/ads1299_driver/YuEEG_UI.h'),'binaries_sha256':{f.name:sha(f) for f in (ROOT/'firmware/build').glob('*.bin')},'protocol_tests_passed':6,'flash_bytes':769761,'static_ram_bytes':46068,'physical_flash_or_transport_tested':False}
(ROOT/'firmware/build/BUILD_INFO.json').write_text(json.dumps(info,indent=2))
patterns=['*.kicad_pro','*.kicad_sch','*.kicad_pcb','*.kicad_dru','*.csv','fp-lib-table','sym-lib-table','README.md','REV_F_REVIEW.md','YuEEG_8CH_RevF.pdf','libraries/*.kicad_sym','footprints/*/*.kicad_mod','models/*','fabrication_review/*','firmware/**/*','review/PCB_3D*.png','review/PCB_top.svg','review/PCB_bottom.svg','review/schematic_contact_sheet.png','review/pcb_drc.json','review/ERC.rpt','review/PCB_validation.json','review/ELECTRICAL_AUDIT.json','review/REV_F_ELECTRICAL_AUDIT.json','review/connectivity_report.json','review/placement_report.json','review/via_in_pad.json','review/netlist.xml','review/expected_connections.json','review/audit_afe_f.py','review/audit_revision_f.py','review/verify_netlist.py','review/sexpr_io.py','review/host_domain_nets.json','review/finalize_delivery_f.py']
auxpatterns=['*.kicad_pro','*.kicad_sch','*.kicad_pcb','*.kicad_dru','*.csv','fp-lib-table','sym-lib-table','YuEEG_8CH_RevF_POWER.pdf','fabrication_review/*','review/pcb_drc.json','review/ERC.rpt','review/PCB_validation.json','review/connectivity_report.json','review/placement_report.json','review/via_in_pad.json','review/netlist.xml','review/expected_connections.json','review/host_domain_nets.json','review/PCB_3D*.png','review/PCB_top.svg','review/PCB_bottom.svg','review/schematic_contact_sheet.png']
files=sorted({q for pattern in patterns for q in ROOT.glob(pattern) if q.is_file()}|{q for pattern in auxpatterns for q in (ROOT/'isolated_power').glob(pattern) if q.is_file()})
manifest={q.relative_to(ROOT).as_posix():sha(q) for q in files};(ROOT/'CHECKSUMS.json').write_text(json.dumps(manifest,indent=2));files.append(ROOT/'CHECKSUMS.json')
out=ROOT.parent/'YuEEG_8CH_RevF_70x80_main_44x48_power_review.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for f in files:z.write(f,Path(ROOT.name)/f.relative_to(ROOT))
# Ignore scratch scripts and stale copied artifacts; only reviewed inventory is published.
rules=['*','!*/','!.gitignore','!CHECKSUMS.json']+['!/'+n for n in manifest]
(ROOT/'.gitignore').write_text('\n'.join(rules)+'\n')
print(json.dumps({'boards':validations,'manifest_files':len(manifest),'archive':str(out)},indent=2))

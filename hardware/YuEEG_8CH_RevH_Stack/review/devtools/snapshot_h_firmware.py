from pathlib import Path
import json,hashlib,shutil,re,datetime
R=Path('hardware/YuEEG_8CH_RevH_Stack');src=Path('Firmware/ads1299_driver');build=Path('Firmware/build_revH');dest=R/'firmware';(dest/'ads1299_driver').mkdir(parents=True,exist_ok=True);(dest/'build').mkdir(exist_ok=True);(dest/'tools').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
code=list(src.glob('*.h'))+list(src.glob('*.cpp'))+list(src.glob('*.ino'));elf=build/'ads1299_driver.ino.elf';assert elf.exists() and all(p.stat().st_mtime<=elf.stat().st_mtime for p in code),'Source changed after compilation'
log=Path('logs/firmware_revH_motion_compile.log').read_text(encoding='utf8');m=re.search(r'Sketch uses (\d+) bytes',log);ram=re.search(r'Global variables use (\d+) bytes',log);assert m and ram
tests=Path('logs/firmware_revH_protocol.log').read_text(encoding='utf8');assert 'Ran 6 tests' in tests and tests.rstrip().endswith('OK')
materials=list(src.glob('*LICENSE*.txt'))
for p in code+materials+list(src.glob('*.md')):
 if p.suffix=='.md':(dest/'ads1299_driver'/p.name).write_text(p.read_text(encoding='utf8').replace('(../../docs/','(../../../../docs/'),encoding='utf8')
 else:shutil.copy2(p,dest/'ads1299_driver'/p.name)
bins={}
for suffix in ['.bin','.bootloader.bin','.partitions.bin']:
 p=build/('ads1299_driver.ino'+suffix);assert p.exists();shutil.copy2(p,dest/'build'/p.name);bins[p.name]=sha(p)
tool_sources={}
for p in Path('Firmware/tools').rglob('*'):
 if p.is_file() and (p.suffix in ['.py','.cpp','.hex'] or p.name=='requirements.txt'):
  name=p.relative_to('Firmware/tools').as_posix();target=dest/'tools'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);tool_sources[name]=sha(p)
motion_tests=Path('logs/firmware_revH_motion_tests.log').read_text(encoding='utf8');assert 'Ran 10 tests' in motion_tests and motion_tests.rstrip().endswith('OK')
relative_tests=Path('logs/relative_motion_tests.log').read_text(encoding='utf8');assert 'PASS 36 relative-motion and wire checks' in relative_tests
shutil.copy2('logs/firmware_revH_motion_tests.log',dest/'build/motion_protocol_tests.log');shutil.copy2('logs/relative_motion_tests.log',dest/'build/relative_motion_tests.log')
shutil.copy2('logs/firmware_revH_protocol.log',dest/'build/protocol_tests.log');shutil.copy2('logs/firmware_revH_motion_compile.log',dest/'build/compile.log')
info={'status':'REV_H_DEVELOPMENT_NOT_FLASHED_OR_RELEASED','battery':'Sony NP-BX1 single cell; loaded-voltage telemetry before boost','timestamp':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'fqbn':'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB','arduino_esp32_core':'2.0.11','source_sha256':{p.name:sha(p) for p in code+materials},'binaries_sha256':bins,'protocol_tests_passed':6,'flash_bytes':int(m[1]),'static_ram_bytes':int(ram[1]),'battery_pin_contract':'../review/firmware_battery_contract.json','physical_flash_or_transport_tested':False,'battery_voltage_calibration_tested':False,'acquisition_timing_with_battery_monitor_tested':False,'imu_part':'SCH16T-K01-1','imu_scope':'DRDY continuous sampling; explicit stationary alignment; arbitrary-yaw3s relative trajectory; sharedSPI3','imu_continuous_sampling_implemented':True,'navigation_implemented':True,'navigation_scope':'RELATIVE_ATTITUDE_3S_UNREFERENCED_NO_UWB','motion_protocol_tests_passed':10,'relative_motion_checks_passed':36,'tools_source_sha256':tool_sources,'motion_tests_sha256':{'motion_protocol_tests.log':sha(dest/'build/motion_protocol_tests.log'),'relative_motion_tests.log':sha(dest/'build/relative_motion_tests.log')},'trajectory_window_seconds':3.0,'imu_hardware_tested':False}
info['imu_upstream']=json.loads((src/'SCH16T_UPSTREAM.json').read_text(encoding='utf8'))
shutil.copy2(src/'SCH16T_UPSTREAM.json',dest/'ads1299_driver/SCH16T_UPSTREAM.json')
(dest/'build/BUILD_INFO.json').write_text(json.dumps(info,indent=2))
(dest/'README.md').write_text('''# Rev H firmware engineering snapshot

This snapshot matches the current NP-BX1 hardware wiring. It includes isolated USB + Wi-Fi output, SD backup, AMOLED status and a separate ADC1 battery telemetry task. SCH16T-K01 DRDY streaming, manually aligned relative attitude and a3s relative trajectory window are included, with USB/UDP9002 and separate SD motion backup. No UWB, absolute heading or bounded long-term position is claimed. Six EEG tests,10 motion-protocol tests and36 actual C++core/wire/gate checks passed. Six host protocol tests and the ESP32-S3 build passed; no Rev H board has been flashed or measured.

`build/BUILD_INFO.json` binds the sources and binary hashes. Read `ads1299_driver/README.md` for exact GPIOs, build settings and limitations. Battery telemetry is protected loaded voltage with nominal divider scaling, not SOC or calibrated cell voltage. The warning does not guarantee an SD flush before hardware cutoff.

Rev G sources and binaries remain in their own frozen hardware folder. This folder is development evidence, not a production firmware release.
''')
print('Snapshot: flash',info['flash_bytes'],'bytes; RAM',info['static_ram_bytes'],'bytes; six protocol tests passed')

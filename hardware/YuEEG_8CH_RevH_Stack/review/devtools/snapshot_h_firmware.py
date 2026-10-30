from pathlib import Path
import json,hashlib,shutil,re,datetime
R=Path('hardware/YuEEG_8CH_RevH_Stack');src=Path('Firmware/ads1299_driver');build=Path('Firmware/build_revH');dest=R/'firmware';(dest/'ads1299_driver').mkdir(parents=True,exist_ok=True);(dest/'build').mkdir(exist_ok=True);(dest/'tools').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
code=list(src.glob('*.h'))+list(src.glob('*.ino'));elf=build/'ads1299_driver.ino.elf';assert elf.exists() and all(p.stat().st_mtime<=elf.stat().st_mtime for p in code),'Source changed after compilation'
log=Path('logs/firmware_revH_compile.log').read_text();m=re.search(r'Sketch uses (\d+) bytes',log);ram=re.search(r'Global variables use (\d+) bytes',log);assert m and ram
tests=Path('logs/firmware_revH_protocol.log').read_text();assert 'Ran 6 tests' in tests and tests.rstrip().endswith('OK')
for p in code+list(src.glob('*.md')):shutil.copy2(p,dest/'ads1299_driver'/p.name)
bins={}
for suffix in ['.bin','.bootloader.bin','.partitions.bin']:
 p=build/('ads1299_driver.ino'+suffix);assert p.exists();shutil.copy2(p,dest/'build'/p.name);bins[p.name]=sha(p)
for name in ['receive_eeg.py','send_eeg_command.py','test_protocol.py','requirements.txt']:shutil.copy2(Path('Firmware/tools')/name,dest/'tools'/name)
shutil.copy2('logs/firmware_revH_protocol.log',dest/'build/protocol_tests.log');shutil.copy2('logs/firmware_revH_compile.log',dest/'build/compile.log')
info={'status':'REV_H_DEVELOPMENT_NOT_FLASHED_OR_RELEASED','battery':'Sony NP-BX1 single cell; loaded-voltage telemetry before boost','timestamp':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'fqbn':'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB','arduino_esp32_core':'2.0.11','source_sha256':{p.name:sha(p) for p in code},'binaries_sha256':bins,'protocol_tests_passed':6,'flash_bytes':int(m[1]),'static_ram_bytes':int(ram[1]),'battery_pin_contract':'../review/firmware_battery_contract.json','physical_flash_or_transport_tested':False,'battery_voltage_calibration_tested':False,'acquisition_timing_with_battery_monitor_tested':False}
(dest/'build/BUILD_INFO.json').write_text(json.dumps(info,indent=2))
(dest/'README.md').write_text('''# Rev H firmware engineering snapshot

This snapshot matches the current NP-BX1 hardware wiring. It includes isolated USB + Wi-Fi output, SD backup, AMOLED status and a separate ADC1 battery telemetry task. Six host protocol tests and the ESP32-S3 build passed; no Rev H board has been flashed or measured.

`build/BUILD_INFO.json` binds the sources and binary hashes. Read `ads1299_driver/README.md` for exact GPIOs, build settings and limitations. Battery telemetry is protected loaded voltage with nominal divider scaling, not SOC or calibrated cell voltage. The warning does not guarantee an SD flush before hardware cutoff.

Rev G sources and binaries remain in their own frozen hardware folder. This folder is development evidence, not a production firmware release.
''')
print('Snapshot: flash',info['flash_bytes'],'bytes; RAM',info['static_ram_bytes'],'bytes; six protocol tests passed')

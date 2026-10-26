"""Verify the frozen Rev E files, source snapshot and ZIP using only Python stdlib.

Use --package to regenerate the ZIP after successful verification of its inputs.
This does not rerun KiCad or certify the hardware.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'hardware/YuEEG_8CH_RevE'
ARCHIVE = ROOT / 'hardware/YuEEG_8CH_RevE_94x122_dual_USB_AMOLED_SD_review.zip'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(package=False):
    manifest = json.loads((REVIEW / 'CHECKSUMS.json').read_text(encoding='utf-8'))
    for name, digest in manifest.items():
        path = REVIEW / name
        require(path.is_file(), f'Missing delivery: {name}')
        require(sha(path.read_bytes()) == digest, f'Changed frozen delivery: {name}')
    validation = json.loads((REVIEW / 'review/PCB_validation.json').read_text())
    require(validation['sha256_pcb'] == sha((REVIEW / 'YuEEG_8CH_RevE.kicad_pcb').read_bytes()), 'Stale PCB validation')
    for name in ('ERC_violations', 'DRC_violations', 'unconnected_items', 'schematic_parity_issues'):
        require(validation[name] == 0, f'Nonzero {name}')
    drc = json.loads((REVIEW / 'review/pcb_drc.json').read_text(encoding='utf-8'))
    require(all(not drc[k] for k in ('violations', 'unconnected_items', 'schematic_parity')), 'DRC report is not clean')
    for name in ('ELECTRICAL_AUDIT.json', 'REV_E_ELECTRICAL_AUDIT.json'):
        audit = json.loads((REVIEW / 'review' / name).read_text())
        require(audit['sha256_pcb'] == validation['sha256_pcb'], f'Stale {name}')
    source_names = [
        'ads1299_driver/ads1299_driver.ino', 'ads1299_driver/YuEEG.h',
        'ads1299_driver/README.md', 'ads1299_driver/YuEEG_UI.h', 'tools/receive_eeg.py',
        'tools/send_eeg_command.py', 'tools/test_protocol.py',
    ]
    for name in source_names:
        require((ROOT / 'Firmware' / name).read_bytes() == (REVIEW / 'firmware' / name).read_bytes(), f'Firmware snapshot differs: {name}')
    build = json.loads((REVIEW / 'firmware/build/BUILD_INFO.json').read_text())
    require(build['source_header_sha256'] == sha((ROOT / 'Firmware/ads1299_driver/YuEEG.h').read_bytes()), 'Build source hash differs')
    require(build['ui_header_sha256'] == sha((ROOT / 'Firmware/ads1299_driver/YuEEG_UI.h').read_bytes()), 'UI build source hash differs')
    for name, digest in build['binaries_sha256'].items():
        require(sha((REVIEW / 'firmware/build' / name).read_bytes()) == digest, f'Binary differs: {name}')
    names = sorted(manifest) + ['CHECKSUMS.json']
    if package:
        with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
            for name in names:
                archive.write(REVIEW / name, REVIEW.name + '/' + name)
    require(ARCHIVE.is_file(), 'Review ZIP missing; use --package')
    with zipfile.ZipFile(ARCHIVE) as archive:
        require(archive.testzip() is None, 'ZIP CRC error')
        require(set(archive.namelist()) == {REVIEW.name + '/' + name for name in names}, 'Unexpected ZIP inventory')
        for name in names:
            require(archive.read(REVIEW.name + '/' + name) == (REVIEW / name).read_bytes(), f'ZIP differs: {name}')
    print(f'PASS: {len(manifest)} delivery hashes, PCB reports, firmware snapshot and {len(names)} ZIP entries.')
    print('Scope: frozen-file integrity; no new KiCad, firmware build or physical validation performed.')


def verify_rev_d():
    directory=ROOT/'hardware/YuEEG_8CH_RevD'
    manifest=json.loads((directory/'CHECKSUMS.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(ROOT/'hardware/YuEEG_8CH_RevD_84x122_isolated_USB_WiFi_review.zip') as archive:
        require(archive.testzip() is None,'Rev D ZIP CRC error')
        for name,digest in manifest.items():
            data=(directory/name).read_bytes()
            require(sha(data)==digest,f'Changed historical Rev D file: {name}')
            require(archive.read(directory.name+'/'+name)==data,f'Rev D ZIP differs: {name}')
    print(f'PASS: historical Rev D remains unchanged ({len(manifest)} hashes).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', action='store_true')
    args = parser.parse_args()
    verify(args.package)
    verify_rev_d()

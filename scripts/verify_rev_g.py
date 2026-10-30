"""Check the Rev G release inventory and report bindings; does not rerun KiCad."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / 'hardware/YuEEG_8CH_RevG'
ARCHIVE = ROOT / 'hardware/YuEEG_8CH_RevG_AM178_review.zip'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(package=False):
    manifest = json.loads((G / 'CHECKSUMS.json').read_text(encoding='utf8'))
    for name, digest in manifest.items():
        require(sha(G / name) == digest, 'Changed Rev G delivery: ' + name)
    for folder, stem, size in [('', 'YuEEG_8CH_RevG', [70, 80]),
                              ('display_carrier', 'YuEEG_DISPLAY_G', [35, 67]),
                              ('isolated_power', 'YuEEG_8CH_RevF_POWER', [44, 48])]:
        base = G / folder
        v = json.loads((base / 'review/PCB_validation.json').read_text())
        require(v['sha256_pcb'] == sha(base / (stem + '.kicad_pcb')), 'Stale PCB report: ' + stem)
        require(v['pcb_envelope_mm'] == size, 'Wrong board size: ' + stem)
        for field in ['ERC_violations', 'DRC_violations', 'unconnected_items', 'schematic_parity_issues']:
            require(v[field] == 0, 'Nonzero ' + field + ': ' + stem)
        d = json.loads((base / 'review/pcb_drc.json').read_text(encoding='utf8'))
        require(all(not d[k] for k in ['violations', 'unconnected_items', 'schematic_parity']), 'Dirty DRC: ' + stem)
    audit = json.loads((G / 'review/REV_G_ELECTRICAL_AUDIT.json').read_text())
    require(audit['main_pcb_sha256'] == sha(G / 'YuEEG_8CH_RevG.kicad_pcb'), 'Stale main audit')
    require(audit['carrier_pcb_sha256'] == sha(G / 'display_carrier/YuEEG_DISPLAY_G.kicad_pcb'), 'Stale carrier audit')
    require(audit['main_tracks_vias_pads_identical_to_rev_f'] and audit['panel_mapping_checked'], 'Audit failed')
    old = ROOT / 'hardware/YuEEG_8CH_RevF'
    require(audit['rev_f_pcb_sha256'] == sha(old / 'YuEEG_8CH_RevF.kicad_pcb'), 'Baseline changed')
    for name, digest in json.loads((old / 'CHECKSUMS.json').read_text()).items():
        if name.startswith('isolated_power/'):
            require(sha(G / name) == digest, 'Changed inherited power board: ' + name)
    # Rev G is frozen. Its manifest above still checks every archived source byte.
    # The active Firmware/ tree may advance to Rev H and is checked separately;
    # requiring it to mirror an older release would forbid intentional development.
    build = json.loads((G / 'firmware/build/BUILD_INFO.json').read_text())
    for field, file in [('source_header_sha256', 'YuEEG.h'), ('ui_header_sha256', 'YuEEG_UI.h')]:
        require(build[field] == sha(G / 'firmware/ads1299_driver' / file), 'Build source mismatch')
    for name, digest in build['binaries_sha256'].items():
        require(sha(G / 'firmware/build' / name) == digest, 'Binary mismatch: ' + name)
    export = json.loads((G / 'order_gerbers/EXPORT_MANIFEST.json').read_text())
    for entry in export:
        require(sha(G / entry['pcb']) == entry['pcb_sha256'], 'Order export PCB mismatch')
        with zipfile.ZipFile(G / entry['zip']) as z:
            require(set(z.namelist()) == set(entry['files']), 'Order ZIP inventory mismatch')
            for name, digest in entry['files'].items():
                data = z.read(name)
                require(hashlib.sha256(data).hexdigest() == digest, 'Order ZIP content mismatch')
                require(data == (G / entry['fabrication'] / name).read_bytes(), 'Order ZIP differs from fabrication')
    names = sorted(manifest) + ['CHECKSUMS.json']
    if package:
        with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as z:
            for name in names:
                z.write(G / name, G.name + '/' + name)
    with zipfile.ZipFile(ARCHIVE) as z:
        require(z.testzip() is None, 'Rev G ZIP CRC error')
        require(set(z.namelist()) == {G.name + '/' + n for n in names}, 'Rev G ZIP inventory mismatch')
        for name in names:
            require(z.read(G.name + '/' + name) == (G / name).read_bytes(), 'Rev G ZIP differs: ' + name)
    print(f'PASS: frozen Rev G {len(manifest)} hashes, three boards, archived firmware and ZIP verified.')


if __name__ == '__main__':
    verify()

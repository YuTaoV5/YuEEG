"""Check the published cage checkpoint's bindings and recorded native scope.

Does not run a CAD kernel, manufacture a part or qualify its physical fit.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import struct

ROOT = Path(__file__).resolve().parents[1]
H = ROOT / 'hardware/YuEEG_8CH_RevH_Stack'
M = H / 'mechanical/current'
D = M / 'battery_cradle'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def verify():
    manifest = read(D / 'MANIFEST.json')
    require(manifest['status'] == 'ENGINEERING_MECHANICAL_PROTOTYPE_NOT_FOR_PRODUCTION', 'Cage must retain its actual release scope')
    names = {f'{part}.{suffix}' for part in ['cradle', 'power_clip', 'rear_jaw'] for suffix in ['step', 'stl']}
    names |= {'cradle_assembly.step', 'cradle_assembly.png', 'native_cad_review.json', 'power_component_envelopes.json', 'clearance_review.json', 'README.md'}
    require(set(manifest['files_sha256']) == names, 'Wrong cage artifact inventory')
    require({p.name for p in D.iterdir()} == names | {'MANIFEST.json'}, 'Unexpected cage delivery; do not include source battery CAD')
    for name, digest in manifest['files_sha256'].items():
        require(sha(D/name) == digest, 'Stale cage artifact: '+name)
    for name, digest in manifest['inputs_sha256'].items():
        require(sha(ROOT/name) == digest, 'Stale cage input: '+name)

    native = read(D/'native_cad_review.json')
    contract = read(M/'battery_cradle_contract.json')
    hardware = read(M/'battery_cradle_hardware.json')
    source = read(M/'npbx1_user_model_comparison.json')
    probe = read(M/'pogo_reference.json')
    require(native['status'] == 'NATIVE_SOLIDS_PASS_SOURCE_MODEL_NOT_PRODUCTION_QUALIFICATION', 'Missing scoped native CAD check')
    require(native['source_geometry_redistributed'] is False and native['source_model_sha256'] == source['source_sha256'], 'Wrong local battery model or publication scope')
    require(native['contract_sha256'] == sha(M/'battery_cradle_contract.json'), 'Stale cage contract')
    require(native['hardware_fact_sha256'] == sha(M/'battery_cradle_hardware.json'), 'Stale hardware drawing facts')
    require(native['key_notch_basis_sha256'] == sha(M/'npbx1_key_notch_basis.json'), 'Stale front-key basis')
    require(native['builder_sha256'] == sha(H/'review/devtools/build_h_battery_cradle.py'), 'Changed native CAD builder')
    require(hardware['nut']['derived_sharp_regular_hex_corner_diameter_max_mm'] <= contract['fastener_requirements']['nut_max_corner_diameter_mm'], 'Nut envelope smaller than drawing-derived corner span')
    require(abs(hardware['nut']['derived_sharp_regular_hex_corner_diameter_max_mm']-4.16/math.cos(math.pi/6)) < 1e-8, 'Nut corner derivation changed')
    require(set(native['parts']) == {'cradle', 'power_clip', 'rear_jaw'}, 'Wrong authored part set')
    for name, part in native['parts'].items():
        require(part['valid'] and part['solid_count'] == 1 and part['volume_mm3'] > 0, 'Invalid or disconnected cage part: '+name)
        for suffix, digest in part['files_sha256'].items():
            require(sha(D/(name+suffix)) == digest, 'Native export binding changed: '+name+suffix)
        # Independently read the exported binary STL rather than trusting its label.
        data = (D/(name+'.stl')).read_bytes()
        facets = struct.unpack_from('<I', data, 80)[0]
        require(facets > 0 and len(data) == 84+50*facets, 'Invalid STL record count: '+name)
        points = []
        for offset in range(84, len(data), 50):
            values = struct.unpack_from('<12fH', data, offset)
            points.extend([values[3:6], values[6:9], values[9:12]])
        bounds = part['bounds_product_mm']
        require(all(math.isfinite(v) and bounds[i]-.05 <= v <= bounds[i+3]+.05 for point in points for i, v in enumerate(point)), 'STL vertices outside authored part envelope: '+name)
    require(len(native['STEP_export_roundtrip_checks']) == 4, 'Missing STEP round trips')
    for row in native['STEP_export_roundtrip_checks']:
        require(row['valid'] and row['solid_count'] == (3 if row['file'] == 'cradle_assembly.step' else 1) and row['volume_error_mm3'] < 1e-4, 'STEP roundtrip failed: '+row['file'])
    require(sha(D/'cradle_assembly.step') == native['assembly_step_sha256'], 'Changed assembly STEP')
    require(len(native['static_battery_checks']) == 3 and len(native['interpart_checks']) == 3, 'Incomplete normal assembly checks')
    require(all(r['battery_overlap_mm3'] < 1e-5 for r in native['static_battery_checks']) and all(r['overlap_mm3'] < 1e-5 for r in native['interpart_checks']), 'Native normal assembly intrusion')
    require(len(native['removal_checks']) == 43 and all(r['maximum_overlap_mm3'] < 1e-5 for r in native['removal_checks']), 'Incomplete or colliding sampled removal')
    require({r['orientation'] for r in native['front_key_checks']} == {'upside_down', 'reverse_end', 'upside_reverse'}, 'Missing wrong-orientation check')
    require(all(r['overlap_if_forced_seated_mm3'] > .01 and 0 <= r['nominal_flat_face_probe_compression_at_block_mm'] < probe['maxstroke_mm'] for r in native['front_key_checks']), 'Native front-key blocking/nominal stroke failed')
    for field, count in [('hardware_space_checks', 48), ('driver_access_space_checks', 16)]:
        require(len(native[field]) == count, 'Incomplete '+field)
        require(all(r['source_battery_overlap_mm3'] < 1e-5 and max(r['part_overlap_mm3'].values()) < 1e-5 for r in native[field]), 'Native fastener/tool interference')
    require(len(native['thread_projection_checks']) == 4 and all(r['shortest_screw_projection_beyond_maximum_budget_nut_mm'] > .4 for r in native['thread_projection_checks']), 'Nominal hardware projection insufficient')

    envelopes = read(D/'power_component_envelopes.json')
    require(envelopes['source_pcb_sha256'] == sha(H/'power/YuEEG_H_POWER.kicad_pcb') and envelopes['extractor_sha256'] == sha(H/'review/devtools/extract_h_cradle_power_envelopes.py'), 'Stale native power envelopes')
    with (H/'power/BOM.csv').open(encoding='utf-8-sig') as stream:
        refs = {r['Reference'] for r in csv.DictReader(stream)}
    require({r['reference'] for r in envelopes['rows']} == refs and len(envelopes['rows']) == 21, 'Incomplete native courtyard coverage')
    clear = read(D/'clearance_review.json')
    require(clear['status'] == 'PASS_CONSERVATIVE_NOMINAL_CLEARANCE_NOT_ASSEMBLY_QUALIFICATION', 'Cage clearance conflict or changed scope')
    for name, digest in clear['input_sha256'].items():
        require(sha(ROOT/name) == digest, 'Stale cage clearance source: '+name)
    require(len(clear['obstacle_checks']) == 26 and all(not r['material_box_intrusions'] for r in clear['obstacle_checks']), 'Incomplete/colliding PCB/component envelope screen')
    require(not clear['power_PCB_foreaft_slot_intrusions'], 'Power slot interference')
    require(len(clear['hardware_to_obstacle_checks']) == 12 and all(not r['intrusions'] for r in clear['hardware_to_obstacle_checks']), 'Hardware to board/component intrusion')
    require(len(clear['wire_checks']) == 4 and all(r['tube_to_holder_lower_bound_mm'] > 0 for r in clear['wire_checks']), 'Wire to holder/hardware interference')
    print('PASS: authored cage STEP/STL bindings, native scope, sampled fit and conditional PCB/component/harness clearance. Physical assembly remains unqualified.')


if __name__ == '__main__':
    verify()

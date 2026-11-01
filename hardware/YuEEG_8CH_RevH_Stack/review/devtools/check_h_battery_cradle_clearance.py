"""Check authored cage against native-XY power envelopes and nominal wire paths.

Pure point/box bounds conservatively retain all material before holes are cut.
No imports of report writers and no modifications to PCB sources.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import sys

sys.path.insert(0, str(Path('logs/mechanical_runtime').resolve()))
import numpy as np

H = Path('hardware/YuEEG_8CH_RevH_Stack')
M = H / 'mechanical/current'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--artifacts', type=Path, default=M/'battery_cradle')
args = parser.parse_args()
O = args.artifacts
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
contract_path = M / 'battery_cradle_contract.json'
contract = json.loads(contract_path.read_text())
native = json.loads((O / 'native_cad_review.json').read_text())
assert native['contract_sha256'] == sha(contract_path)
envelopes = json.loads((O / 'power_component_envelopes.json').read_text())
assert envelopes['source_pcb_sha256'] == sha(H / 'power/YuEEG_H_POWER.kicad_pcb')
harness_path = M / 'complete_power_harness_review.json'
harness = json.loads(harness_path.read_text())

def box_distance(a, b):
    a, b = np.array(a), np.array(b)
    gap = np.maximum(np.maximum(b[:3]-a[3:], a[:3]-b[3:]), 0)
    penetration = np.minimum(a[3:], b[3:])-np.maximum(a[:3], b[:3])
    return float(np.linalg.norm(gap)), bool(np.all(penetration > 1e-8))

# Check the full specified rear-jaw adjustment travel, not only this source pack.
material_boxes = []
for part, spec in contract['parts'].items():
    for feature, bb in spec['add_boxes']:
        b = list(bb)
        if part == 'rear_jaw':
            b[1] -= .5
            b[4] += .5
        material_boxes.append((part+'/'+feature, b))

obstacles = [
    ('AFE_substrate', [0, 0, -1.6, 48, 60, 0]),
    ('digital_substrate', [0, 0, 8.5, 48, 60, 10.1]),
    ('power_substrate', [49.95, -4.05, -1.4, 83.95, -3.05, 16.6]),
    ('power_PH4_mated_reference', [49.45, -9.55, -.75, 60.65, -4.05, 11.15]),
    ('conditional_flat_screen', [6, .4, 16.1, 40.14, 43.14, 18.88]),
]
obstacles += [('power_'+row['reference'], row['product_prism_mm']) for row in envelopes['rows']]
rows = []
for name, bb in obstacles:
    measures = [(box_distance(bb, b), feature) for feature, b in material_boxes]
    gap, feature = min((g[0], f) for g, f in measures)
    hits = [f for (g, f) in measures if g[1]]
    rows.append({'obstacle': name, 'bounds_product_mm': bb, 'minimum_box_gap_mm': gap,
                 'closest_holder_feature': feature, 'material_box_intrusions': hits})

# Native power board may shift +/-0.1 mm in Y inside its retaining slot.
# This is designed slot play, not a supplier thickness or manufacture tolerance.
slot = [49.95, -4.15, -1.4, 83.95, -2.95, 16.6]
slot_hits = [f for f, b in material_boxes if box_distance(slot, b)[1]]

# Reuse just the existing side-effect-free analytic sampler, with its explicit
# ds/numpy/math dependencies. Do not execute the parent report writer.
sampler_path = H / 'review/devtools/review_h_complete_power_harness.py'
tree = ast.parse(sampler_path.read_text())
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'sample')
ds = harness['sampling_max_axis_step_mm']
namespace = {'np': np, 'math': math, 'ds': ds}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(sampler_path), 'exec'), namespace)
sample = namespace['sample']
od = harness['assumptions']['wire_OD_max_mm']
wire_rows = []
for wire in harness['wires']:
    chunks = [sample(s) for s in wire['segments']]
    assert all(np.linalg.norm(a[-1]-b[0]) < 1e-8 for a, b in zip(chunks, chunks[1:]))
    points = np.concatenate([chunks[0]]+[c[1:] for c in chunks[1:]])
    assert np.max(np.linalg.norm(np.diff(points, axis=0), axis=1)) <= ds*1.00001
    distances = []
    hardware_boxes = [(r['feature'], r['bounds_product_mm']) for r in native['hardware_space_checks'] if r['jaw_adjustment_Y_mm'] == 0.]
    for feature, bb in material_boxes + hardware_boxes:
        b = np.array(bb)
        v = np.maximum(np.maximum(b[:3]-points, points-b[3:]), 0)
        distances.append((float(np.linalg.norm(v, axis=1).min())-od/2-ds/2, feature))
    gap, closest = min(distances)
    wire_rows.append({'pin': wire['pin'], 'net': wire['net'],
                      'sample_count': len(points), 'tube_to_holder_lower_bound_mm': gap,
                      'closest_holder_feature': closest})

hardware_obstacles = []
for hardware, bb in hardware_boxes:
    checks = [(box_distance(bb, ob), name) for name, ob in obstacles]
    gap, name = min((d[0], name) for d, name in checks)
    hardware_obstacles.append({'hardware': hardware, 'minimum_obstacle_gap_mm': gap,
        'closest_obstacle': name, 'intrusions': [name for d, name in checks if d[1]]})
hits = [r for r in rows if r['material_box_intrusions']]
ok = not hits and not slot_hits and not any(r['intrusions'] for r in hardware_obstacles) and min(r['tube_to_holder_lower_bound_mm'] for r in wire_rows) > 0
portable_inputs = {str(p).replace('\\', '/'): sha(p) for p in [contract_path, harness_path, sampler_path, M/'pogo_reference.json', Path(__file__)] + [H/board/('YuEEG_H_'+board.upper()+'.kicad_pcb') for board in ['afe', 'digital', 'power']]}
portable_inputs.update({str(M/'battery_cradle'/name).replace('\\', '/'): sha(O/name) for name in ['native_cad_review.json', 'power_component_envelopes.json']})
report = {
    'status': 'PASS_CONSERVATIVE_NOMINAL_CLEARANCE_NOT_ASSEMBLY_QUALIFICATION' if ok else 'CLEARANCE_CONFLICTS_REQUIRE_DESIGN_CHANGE',
    'input_sha256': portable_inputs,
    'part_checks_use_uncut_positive_material_boxes': True,
    'rear_jaw_Y_adjustment_range_mm': [-.5, .5],
    'obstacle_checks': rows,
    'power_PCB_foreaft_slot_swept_box_product_mm': slot,
    'power_PCB_foreaft_slot_intrusions': slot_hits,
    'wire_checks': wire_rows,
    'hardware_to_obstacle_checks': hardware_obstacles,
    'wire_bound_method': 'Analytic curve samples step<=0.02 mm; point-to-positive-material-box minus wire OD/2 and maximum sample step/2. Entire jaw adjustment travel included. Holes omitted conservatively.',
    'scope': 'Source-bound native power courtyards with imposed height budgets, PCB substrates, conditional PH4/screen boxes and existing nominal harness paths. No actual component CAD, screen-back/folded FPC datum, solder, part/placement/cable tolerances, strain relief, holder fixation to enclosure, fastener clearance/strength or complete electrical isolation qualification.'}
(O/'clearance_review.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(report['status'])
print('Obstacle conflicts:', [(r['obstacle'], r['material_box_intrusions']) for r in hits])
print('Power PCB slot conflicts:', slot_hits)
print('Wire gaps:', [(r['pin'], round(r['tube_to_holder_lower_bound_mm'], 4), r['closest_holder_feature']) for r in wire_rows])
assert ok, 'Revise the cage instead of weakening the clearance check'

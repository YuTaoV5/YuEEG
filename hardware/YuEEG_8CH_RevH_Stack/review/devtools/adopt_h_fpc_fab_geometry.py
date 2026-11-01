"""Adopt the isolated, DRC-clean FPC edge-clearance candidate once.

Only the upper taper, four GND segments, DRC constraints and fabrication
drawings change. Main boards and connector pads remain untouched.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import uuid
import pcbnew as p
import wx

wx.DisableAsserts()
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--candidate', required=True, type=Path)
args = ap.parse_args()
H = Path('hardware/YuEEG_8CH_RevH_Stack'); D = H/'display_link'
stem = 'YuEEG_H_DISPLAY_LINK'; target = D/(stem+'.kicad_pcb')
candidate = args.candidate/(stem+'.kicad_pcb')
sha = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(target) == '51979b486cb4e063baf91e5e389caad5001929970646c76e1cca3f596b3a5b12', 'Already adopted or changed baseline; do not overwrite it'
baseline_sha = sha(target)
sys.path.insert(0, str(Path('hardware/YuEEG_8CH_RevG/review').resolve()))
from sexpr_io import loads, dumps, sub

# F.Adhes carries actual filled stiffener regions, not a stroke-width allowance.
tree = loads(candidate.read_text())
stiffeners = 0
for node in tree:
    if isinstance(node, list) and node[0] == 'gr_rect' and sub(node, 'layer')[1] == '"F.Adhes"':
        sub(node, 'fill')[1] = 'solid'; sub(sub(node, 'stroke'), 'width')[1] = '0'
        stiffeners += 1
assert stiffeners == 2
notes = [
    'PI FLEX ENGINEERING PROTOTYPE / NOT FOR ORDER',
    'TARGET: PI core25um; base Cu12um/side; finished0.11mm nominal',
    'F.Adhes: F-side PI stiffener0.20mm proposed / filled regions',
    'B.Mask: gang coverlay windows / both connectors on B',
    'Final coverlay, plating, laminate and stiffener tolerances: fab approval pending',
]
tree[:] = [node for node in tree if not (isinstance(node, list) and node[0] == 'gr_text' and json.loads(node[1]) in notes)]
for i, text in enumerate(notes):
    tree.append(['gr_text', json.dumps(text), ['at', '12', str(1+i*1.8)],
                 ['layer', '"Cmts.User"'], ['uuid', json.dumps(str(uuid.uuid4()))],
                 ['effects', ['font', ['size', '.7', '.7'], ['thickness', '.1']], ['justify', 'left']]])
candidate.write_text(dumps(tree), encoding='utf8')
candidate_pro = args.candidate/(stem+'.kicad_pro')
candidate_pro_bytes = candidate_pro.read_bytes()
filled = p.LoadBoard(str(candidate))
for zone in filled.Zones():
    if not zone.GetIsRuleArea(): zone.SetLocalClearance(p.FromMM(.15))
p.ZONE_FILLER(filled).Fill(filled.Zones())
p.SaveBoard(str(candidate), filled); candidate_pro.write_bytes(candidate_pro_bytes)
(args.candidate/(stem+'.kicad_dru')).write_text('''(version 1)
(rule "Exposed connector pad to other-net copper"
 (condition "A.Type == 'Pad' || B.Type == 'Pad'")
 (constraint clearance (min 0.15mm)))
''', encoding='utf8')

def xy(v): return [p.ToMM(v.x), p.ToMM(v.y)]
def footprints(board):
    return {f.GetReference(): {'xy': xy(f.GetPosition()), 'angle': f.GetOrientationDegrees(),
        'layer': f.GetLayer(), 'value': f.GetValue(), 'library': f.GetFPID().GetLibItemName(),
        'pads': sorted([{'pin': v.GetNumber(), 'xy': xy(v.GetPosition()), 'size': xy(v.GetSize()),
                         'angle': v.GetOrientationDegrees(), 'net': v.GetNetname(), 'layer': v.GetLayer(),
                         'attribute': v.GetAttribute(), 'shape': v.GetShape()} for v in f.Pads()], key=lambda r: int(r['pin']))}
        for f in board.GetFootprints()}
def tracks(board):
    rows = {}
    for t in board.GetTracks():
        row = {'net': t.GetNetname(), 'width': p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t, p.PCB_VIA) else t.GetWidth())}
        if isinstance(t, p.PCB_VIA): row.update(kind='via', at=xy(t.GetPosition()), drill=p.ToMM(t.GetDrillValue()))
        else: row.update(kind='track', start=xy(t.GetStart()), end=xy(t.GetEnd()), layer=t.GetLayer())
        rows[t.m_Uuid.AsString()] = row
    return rows
old_board = p.LoadBoard(str(target)); new_board = p.LoadBoard(str(candidate))
assert footprints(old_board) == footprints(new_board), 'Connector poses, pad geometry or nets changed'
old_tracks, new_tracks = tracks(old_board), tracks(new_board)
assert old_tracks.keys() == new_tracks.keys()
changes = []
for key, old in old_tracks.items():
    new = new_tracks[key]
    if old == new: continue
    assert old['kind'] == new['kind'] == 'track' and old['net'] == new['net'] == 'GND'
    for field in ['net', 'width', 'kind', 'layer']: assert old[field] == new[field]
    for field in ['start', 'end']:
        if old[field] != new[field]:
            assert abs(old[field][0]-1.9) < .000002 and new[field][0] == 1.91 and old[field][1] == new[field][1]
    changes.append({'uuid': key, 'before': old, 'after': new})
assert len(changes) == 4
old_pro = json.loads((D/(stem+'.kicad_pro')).read_text())
new_pro = json.loads((args.candidate/(stem+'.kicad_pro')).read_text())
expected = json.loads(json.dumps(old_pro)); expected['board']['design_settings']['rules']['min_copper_edge_clearance'] = .3
assert expected == new_pro
q = json.loads((D/'review/design_contract.json').read_text())
assert q['end_taper_offsets_from_connector_mm'] == [1.55, 2.05]
q['end_taper_offsets_by_connector_mm'] = {'JF1': [1.55, 2.05], 'JF2': [1.65, 2.05]}
q['fabrication_proposal'] = 'Two-layer PI FPC;25um polyimide core and12um base copper per side, nominal .11mm finished yellow-coverlay target. Individual coverlay/adhesive/plating thickness allocation not factory-approved; no invented numeric KiCad laminate stack. F-side .20mm PI stiffeners are proposed filled F.Adhes regions. Advanced .10/.30mm vias, gang coverlay windows and final stackup, tolerances, support and assembly process need fabricator confirmation.'
q['material_declaration_layer'] = 'Cmts.User'
q['stiffener_definition'] = {'layer': 'F.Adhes', 'side': 'F', 'material': 'PI', 'proposed_thickness_mm': .20, 'filled_regions': True}
q['minimum_copper_edge_clearance_mm'] = .3
q['exposed_SMD_pad_to_other_net_copper_clearance_mm'] = .15

cli = 'X:/SoftWare/Kicad/bin/kicad-cli.exe'
proof = args.candidate/'drc_adoption.json'
subprocess.run([cli, 'pcb', 'drc', '--schematic-parity', '--format', 'json', '-o', str(proof), str(candidate)], check=True, stdout=subprocess.DEVNULL)
drc = json.loads(proof.read_text(encoding='utf8'))
assert all(not drc[k] for k in ['violations', 'unconnected_items', 'schematic_parity'])
main = {name: sha(H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb')) for name in ['afe', 'digital', 'power']}
for suffix in ['.kicad_pcb', '.kicad_pro', '.kicad_dru']:
    shutil.copyfile(args.candidate/(stem+suffix), D/(stem+suffix))
(D/'review/design_contract.json').write_text(json.dumps(q, indent=2), encoding='utf8')
record = {'status': 'FPC_DFM_GEOMETRY_ADOPTED_NOT_ASSEMBLY_OR_FAB_RELEASE',
    'baseline_pcb_sha256': baseline_sha, 'current_pcb_sha256': sha(target),
    'all_56_pad_geometry_nets_and_both_connector_poses_unchanged': True,
    'only_GND_four_track_endpoint_adjustments': changes, 'all_vias_unchanged': True,
    'upper_taper_start_offset_from_connector_mm': [1.55, 1.65],
    'lower_taper_and_connector_placement_unchanged': True,
    'DRC_constraints': {'copper_edge_minimum_mm': .3, 'SMD_pad_other_net_copper_mm': .15},
    'flat_end_ground_pour_clearance_mm': [.1, .15],
    'checks': {k: len(drc[k]) for k in ['violations', 'unconnected_items', 'schematic_parity']},
    'main_pcb_sha256': main, 'main_pcbs_changed': False,
    'adoption_script_sha256': sha(Path(__file__)),
    'scope': 'Upper end locally widened for retaining-pad/edge clearance;4 GND segments shifted X1.899999/1.9->1.91mm; flat end pours refilled with.15mm clearance and all SMD-pad/other-net copper constrained to.15mm. No electrical or main-board changes. Stiffeners now filled zero-stroke regions and PI fabrication targets explicitly annotated outside board. No approved per-layer laminate, folded-screen Z datum, part mating, manufacturing tolerance or full assembly release.'}
(D/'review/fab_geometry_adoption.json').write_text(json.dumps(record, indent=2), encoding='utf8')
print('Adopted FPC: .30mm edge and .15mm exposed-pad/copper DRC clean;4 GND segment edits; all56 pads/poses and main PCBs unchanged')

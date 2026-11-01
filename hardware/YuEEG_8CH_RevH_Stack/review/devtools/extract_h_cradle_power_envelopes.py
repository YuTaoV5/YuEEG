"""Read native power-board courtyards for conservative cage collision checks.

Uses KiCad's bundled Python; does not modify a PCB or existing review reports.
The 5.5 mm outward courtyard prisms are imposed clearance budgets, not part CAD.
"""
from pathlib import Path
import argparse
import hashlib
import json
import pcbnew as p
import wx

wx.DisableAsserts()
H = Path('hardware/YuEEG_8CH_RevH_Stack')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=H/'mechanical/current/battery_cradle/power_component_envelopes.json')
args = parser.parse_args()
source = H / 'power/YuEEG_H_POWER.kicad_pcb'
board = p.LoadBoard(str(source))
rows = []
missing = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if not ref:
        continue
    layer = p.B_CrtYd if fp.IsFlipped() else p.F_CrtYd
    outlines = [g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer() == layer]
    if not outlines:
        missing.append(ref)
        continue
    x0 = min(p.ToMM(b.GetX()) for b in outlines)
    y0 = min(p.ToMM(b.GetY()) for b in outlines)
    x1 = max(p.ToMM(b.GetRight()) for b in outlines)
    y1 = max(p.ToMM(b.GetBottom()) for b in outlines)
    # JP1's full courtyard becomes a generous common probe box. It is not
    # treated as two narrow cylinders, which would hide base-body collisions.
    product_y = [-3.05, 1.45] if fp.IsFlipped() else [-9.55, -4.05]
    rows.append({'reference': ref, 'side': 'B' if fp.IsFlipped() else 'F',
                 'native_courtyard_xy_mm': [x0, y0, x1, y1],
                 'product_prism_mm': [49.95+x0, product_y[0], 16.6-y1,
                                      49.95+x1, product_y[1], 16.6-y0]})
assert len(rows) == 21 and not missing, (len(rows), missing)
out = args.output
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'status': 'NATIVE_XY_WITH_IMPOSED_HEIGHT_BUDGETS',
    'extractor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'source_pcb_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'outward_height_budget_mm': 5.5, 'probe_free_height_nominal_mm': 4.5,
    'rows': sorted(rows, key=lambda r: r['reference']),
    'scope': 'Every electrical footprint courtyard including line width, transformed from native power PCB. F heights are clearance budgets rather than manufacturer maximum component heights. B JP1 uses its combined courtyard and nominal free height. No real part-shape, solder or tolerance qualification.'}, indent=2), encoding='utf8')
print('Extracted', len(rows), 'native power courtyards; PCB read-only')

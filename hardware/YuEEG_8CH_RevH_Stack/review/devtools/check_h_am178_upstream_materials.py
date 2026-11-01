"""Compare a local, already downloaded official source checkout read-only.

Only trusted git and Poppler are executed; upstream firmware is never run.
The report records provenance and rendered differences, not a shipping SKU or
an inferred folded-FPC Z dimension. Supplier originals stay out of delivery.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as E
from urllib.parse import quote

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--upstream', required=True, type=Path)
parser.add_argument('--renderer', type=Path, default=shutil.which('pdftoppm'))
parser.add_argument('--runtime', type=Path, default=Path('logs/mechanical_runtime'))
parser.add_argument('--scratch', type=Path, default=Path('logs/am178_upstream_renders'))
args = parser.parse_args()
if args.runtime.exists():
    sys.path.insert(0, str(args.runtime.resolve()))
from PIL import Image

H = Path('hardware/YuEEG_8CH_RevH_Stack')
local = Path('hardware/display-amoled-1.78inch-368x448-main')
reference = json.loads((H/'review/am178_vendor_mechanical_review.json').read_text())
digest = lambda data: hashlib.sha256(data).hexdigest()
git = lambda *a: subprocess.check_output(['git', '-C', str(args.upstream), *a])
origin = git('config', '--get', 'remote.origin.url').decode().strip()
assert origin == 'https://github.com/osptek/display-amoled-1.78inch-368x448.git'
commit = git('rev-parse', 'HEAD').decode().strip()
assert commit == '9f68afe8910a2cc10f9c36f36c7b3ed9bb67ec70', 'Different upstream commit; inspect its changes before updating this reviewed comparison'
commit_date = git('show', '-s', '--format=%cI', 'HEAD').decode().strip()
paths = sorted(p.decode('utf8') for p in git('ls-tree', '-rz', '--name-only', 'HEAD').split(b'\0') if p)
binary_extensions = {'.pdf', '.dwg', '.png', '.jpg', '.jpeg', '.webp'}
rows = []
for name in paths:
    blob = git('show', 'HEAD:'+name)
    old_path, new_path = local/name, args.upstream/name
    assert new_path.is_file(), ('Missing checkout file', name)
    new = new_path.read_bytes()
    binary = Path(name).suffix.lower() in binary_extensions
    assert (new if binary else new.replace(b'\r\n', b'\n')) == (blob if binary else blob.replace(b'\r\n', b'\n')), ('Modified source checkout', name)
    old = old_path.read_bytes() if old_path.exists() else None
    same = old == blob
    eol_same = old is not None and not binary and old.replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n')
    rows.append({'path': name, 'upstream_blob_sha256': digest(blob),
                 'local_reference_sha256': digest(old) if old is not None else None,
                 'comparison': 'BYTE_IDENTICAL' if same else 'TEXT_EOL_ONLY' if eol_same else 'CHANGED_CONTENT_OR_CONTAINER',
                 'upstream_url': 'https://github.com/osptek/display-amoled-1.78inch-368x448/blob/'+commit+'/'+quote(name, safe='/')})

pdf = 'versions/AM178Q368448LK/datasheets/AM178Q368448LK.pdf'
dwg = 'versions/AM178Q368448LK/cad/AM178Q368448LK1.dwg'
connector = 'versions/AM178Q368448LK/cad/OK-14F024-04.pdf'
assert digest((local/pdf).read_bytes()) == reference['source_pdf_sha256']
assert digest((local/dwg).read_bytes()) == reference['local_vendor_dwg_sha256']
assert args.renderer and args.renderer.is_file(), 'Provide the trusted Poppler pdftoppm executable'
args.scratch.mkdir(parents=True, exist_ok=True)
stderr = {}
for label, source in [('local', local/pdf), ('upstream', args.upstream/pdf)]:
    run = subprocess.run([str(args.renderer), '-scale-to', '1600', '-png', str(source), str(args.scratch/label)], capture_output=True)
    assert run.returncode == 0, ('Renderer failed', label, run.stderr.decode(errors='replace'))
    stderr[label] = sorted(set(run.stderr.decode(errors='replace').splitlines()))
render_checks = []
for index in range(1, 12):
    a = Image.open(args.scratch/('local-%02d.png'%index)).convert('RGB')
    b = Image.open(args.scratch/('upstream-%02d.png'%index)).convert('RGB')
    render_checks.append({'page': index, 'render_size_px': list(a.size),
        'same_rendered_RGB': a.size == b.size and a.tobytes() == b.tobytes(),
        'local_RGB_sha256': digest(a.tobytes()), 'upstream_RGB_sha256': digest(b.tobytes())})
selected = {r['path']: r for r in rows if r['path'] in [pdf, dwg, connector]}
assert selected[dwg]['comparison'] == selected[connector]['comparison'] == 'BYTE_IDENTICAL', 'Mechanical source changed; inspect before retaining prior review'
changed_pages = [r['page'] for r in render_checks if not r['same_rendered_RGB']]
assert changed_pages == [6], 'Unreviewed PDF page change; inspect before retaining prior review'
# Page6 has been inspected side by side: VDDIO Max1.95 ->3.35 V; its printed
# revision table remains V1.0/2024-03-16. Do not use this to relax the hardware.
netlist = H/'digital/review/netlist.xml'
root = E.parse(netlist)
component = next(n for n in root.findall('./components/comp') if n.get('ref') == 'U1003')
assert component.findtext('value') == 'TPS7A2018PDBVR'
net = {node.get('ref')+'.'+node.get('pin'): row.get('name') for row in root.findall('./nets/net') for node in row.findall('node')}
assert all(net[pin] == 'AM_1V8' for pin in ['U1003.5', 'U1004.23', 'U1004.24', 'J2002.15'])
record = {
    'status': 'UPSTREAM_MECHANICAL_MATCH_ELECTRICAL_VARIANT_REVIEWED_NOT_RELEASE',
    'observed_date': '2026-11-01', 'official_repository': origin,
    'commit': commit, 'commit_date': commit_date,
    'upstream_file_count': len(paths), 'local_reference_file_count': sum(p.is_file() for p in local.rglob('*')),
    'new_upstream_paths': [r['path'] for r in rows if r['local_reference_sha256'] is None],
    'files': rows, 'selected_mechanical_sources': selected,
    'renderer_scale_to_px': 1600, 'renderer_warnings': stderr,
    'render_checks': render_checks,
    'changed_render_pages': changed_pages,
    'mechanical_pages_visual_review': [4, 5],
    'electrical_difference_review': {
        'page': 6, 'local_VDDIO_min_typ_max_V': [1.7, 1.8, 1.95],
        'upstream_VDDIO_min_typ_max_V': [1.7, 1.8, 3.35],
        'printed_revision_record': 'V1.0 preliminary first release2024-03-16; unchanged in both renders',
        'interpretation': 'One visually identified table change; no new explicit PCN or actual shipped-part voltage qualification inferred.',
        'current_regulator': component.findtext('value'), 'current_nominal_VDDIO_V': 1.8,
        'native_exported_pins': {pin: net[pin] for pin in ['U1003.5', 'U1004.23', 'U1004.24', 'J2002.15']},
        'native_netlist_sha256': digest(netlist.read_bytes()),
        'digital_pcb_sha256': digest((H/'digital/YuEEG_H_DIGITAL.kicad_pcb').read_bytes()),
        'hardware_rail_or_level_shift_changed': False,
        'scope': 'Current nominal1.8V rail and level-shifter supply satisfy both displayed VDDIO ranges; this is not output tolerance, startup/overshoot, shipping-SKU or functional qualification.'},
    'current_review_sha256': digest((H/'review/am178_vendor_mechanical_review.json').read_bytes()),
    'source_frozen_pdf_sha256': digest((H.parent/'YuEEG_8CH_RevG/reference/AM178Q368448LK.pdf').read_bytes()),
    'checker_sha256': digest(Path(__file__).read_bytes()),
    'folded_male_solder_plane_to_screen_back_Z_offset_mm': None,
    'source_PDF_or_DWG_copied_to_delivery': False,
    'scope': 'Official git commit fetched read-only, canonical blobs compared with user-provided material;10 of11 PDF pages RGB-identical at1600px, including mechanical4/5. Changed page6 visually reviewed, VDDIO Max1.95->3.35V recorded with unchanged1.8V design. DWG and OCN connector PDF byte-identical. Poppler font warnings retained; relevant labels reviewed against existing DWG audit. No inferred depth from photographs, actual SKU confirmation, complete electrical/physical fit, support height or insulation qualification.'}
(H/'review/am178_upstream_materials_review.json').write_text(json.dumps(record, indent=2), encoding='utf8')
print('PASS', commit, len(rows), 'files;10 of11 PDF pages identical; page6 VDDIO variant reviewed, unchanged1.8V design; no new folded-Z datum')
print('Substantive/container differences:', [r['path'] for r in rows if r['comparison'] == 'CHANGED_CONTENT_OR_CONTAINER'])

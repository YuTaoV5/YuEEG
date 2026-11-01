"""Extract selected dimensions from a local LibreDWG JSON decode of vendor CAD.

Read-only source investigation, not a folded-screen solid or assembly approval.
Run dwgread 0.14 -O JSON -o logs/model_sources/AM178_dwg.json <vendor.dwg>
before this script. The converter is not included in the delivery.
"""
from pathlib import Path
import collections
import hashlib
import json
import re

H = Path('hardware/YuEEG_8CH_RevH_Stack')
source = Path('hardware/display-amoled-1.78inch-368x448-main/versions/AM178Q368448LK')
dwg = source / 'cad/AM178Q368448LK1.dwg'
pdf = Path('hardware/YuEEG_8CH_RevG/reference/AM178Q368448LK.pdf')
decoded = Path('logs/model_sources/AM178_dwg.json')
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
raw = decoded.read_text(encoding='utf8')
# LibreDWG emits lower-case nan in nine non-geometry object fields. Retain the
# raw output locally; normalize only the parser input, never any source CAD.
raw, nonfinite_count = re.subn(r'(?m)^(\s*)-?nan(,?)$', r'\1null\2', raw)
objects = json.loads(raw)['OBJECTS']
assert len(objects) == 15312
counts = collections.Counter(q.get('entity') for q in objects if q.get('entity'))
assert not any(counts[k] for k in ['3DSOLID', 'BODY', 'REGION', 'SURFACE', 'MESH', '3DFACE'])
by_index = {q['index']: q for q in objects}
selected = []
for index, expected, meaning in [
    (14906, 34.14441752205403, 'front-view outer width; drawing rounded 34.14 +/- .04'),
    (14911, 42.74440211499994, 'front-view outer length; drawing rounded 42.74 +/- .04'),
    (15005, 2.58, 'side-view ATC glass/module stack thickness; not folded-FPC overall height'),
    (14992, .805, 'panel outline thickness explicitly excludes protective film and FPC'),
    (14553, .8, 'folded back-view in-plane lower-edge overhang; not a Z height'),
    (14556, .79793534099565, 'second folded back-view in-plane lower-edge overhang'),
    (14565, 21.97983296380146, 'folded back-view in-plane connector position'),
    (14568, 9.95289956028182, 'folded back-view in-plane connector position'),
]:
    q = by_index[index]
    assert q['entity'] == 'DIMENSION_LINEAR'
    assert abs(q['act_measurement'] - expected) < 1e-8
    selected.append({k: q[k] for k in ['index', 'handle', 'act_measurement', 'user_text', 'xline1_pt', 'xline2_pt']})
    selected[-1]['interpretation'] = meaning
contract = H / 'display_link/review/design_contract.json'
out = {
    'status': 'VENDOR_DRAWING_REVIEW_NOT_ASSEMBLY_RELEASE',
    'source_pdf': pdf.as_posix(), 'source_pdf_sha256': sha(pdf),
    'source_pdf_public_url': 'https://yuyinglcd.com/strapi-uploads/AM_178_Q368448_LK_73cb5aa60f.pdf',
    'vendor_product_url': 'https://yuyinglcd.com/products/2/5/493',
    'local_vendor_dwg': dwg.as_posix(), 'local_vendor_dwg_sha256': sha(dwg),
    'local_vendor_dwg_bytes': dwg.stat().st_size,
    'converter': {'name': 'GNU LibreDWG', 'version': '0.14', 'official_release': 'https://github.com/LibreDWG/libredwg/releases/tag/0.14', 'win64_zip_sha256': '1ad7e15344d20b3426c3435b078d82fb84b35062815946b2cca9c5fc9810fea8', 'decode_log': 'SUCCESS; JSON nonfinite metadata normalized to null for parsing', 'nonfinite_values_normalized': nonfinite_count},
    'decoded_objects': len(objects), 'entity_counts': dict(counts),
    'selected_native_dimensions': selected,
    'pdf_page5_visual_observations': {
        'ATC_mm': 2.58, 'ATC_tolerance_mm': .2,
        'outer_width_mm': 34.14, 'outer_length_mm': 42.74,
        'component_fpc_steel_insulation_local_stack_maxima_mm': [1., 1.2],
        'local_stack_maxima_datum': 'Local layers listed in the callout, not complete folded assembly above the screen back.',
        'steel_stiffener_callouts_mm': [.1, .2],
        'adhesive_callout_mm': .05,
        'factory_ships_folded': True,
        'folded_male_solder_plane_to_screen_back_Z_offset_mm': None,
        'complete_folded_back_conductive_envelope_qualified': False,
    },
    'display_link_contract_sha256': sha(contract),
    'connector_mounting_plane_separation_target_mm': json.loads(contract.read_text())['connector_mounting_plane_separation_target_mm'],
    'mechanical_decision': 'Keep screen on top and use a separate insulating support. Do not equate the 6mm flex-plane target with the support height. Current factory 2D CAD and PDF do not close the folded connector Z datum; retain engineering prototype status.',
    'scope': 'Selected numeric DWG entities cross-checked against rendered manufacturer PDF pages4/5. No full CAD solid reconstruction, delivered-SKU equivalence, complete folded assembly clearance or physical validation claimed. The public product table has an inconsistent 35.14mm outer length; use the drawing 42.74mm. The local DWG is not added to this review delivery.',
}
(H / 'review/am178_vendor_mechanical_review.json').write_text(json.dumps(out, indent=2), encoding='utf8')
print('AM178: native 2D dimensions extracted; local stack limits found; folded Z datum remains unspecified.')

"""Bind current power review images to their inputs; do not overwrite maintained devtools."""
from pathlib import Path
import json,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');M=H/'mechanical/current';q=M/'power_port_tail_review.json';d=json.loads(q.read_text());d['minimum_local_surface_gap_required_mm']=8.2;d['conditional_clearance_at_minimum_local_gap_mm']=.8;q.write_text(json.dumps(d,indent=2),encoding='utf8')
files=['power_ports_native.json','power_harness_routing_review.json','power_harness_routing_review.png','power_harness_routing_review.svg','power_port_tail_review.json','complete_power_harness_review.json','complete_power_harness_review.png','complete_power_harness_review.svg']
record=dict(status='CONDITIONAL_REVIEW_ARTIFACTS_NOT_ASSEMBLY_RELEASE',files_sha256={name:hashlib.sha256((M/name).read_bytes()).hexdigest() for name in files},pcb_sha256={name:hashlib.sha256((H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb')).read_bytes()).hexdigest() for name in ['afe','digital','power']},scope='Binds engineering reports and plan-view image artifacts. No measurement, thermal/EEG validation or production release.')
(M/'power_harness_artifacts.json').write_text(json.dumps(record,indent=2),encoding='utf8');print('Power port review tools and artifact bindings finalized')

"""Check migration payload integrity; explicitly does not validate the AM200 PCB."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
H=ROOT/'hardware/YuEEG_8CH_RevH_Stack'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 vendor=H/'reference/am200'
 manifest=json.loads((vendor/'SOURCE_MANIFEST.json').read_text(encoding='utf8'))
 assert manifest['selected_panel']=='AM200Q460460LK'
 for row in manifest['files']:
  p=vendor/row['path']
  assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],p
 state=json.loads((H/'display_am200/review/HANDOFF_CHECKPOINT.json').read_text(encoding='utf8'))
 assert state['status']=='WIP_INCONSISTENT_CONTRACT_AND_PCB_NOT_FOR_ORDER'
 for name,digest in state['files_sha256'].items():
  assert sha(ROOT/name)==digest,'Changed migration file: '+name
 d=json.loads((H/'display_am200/review/drc_current.json').read_text(encoding='utf8'))
 assert len(d['violations'])==22 and len(d['unconnected_items'])==11 and not d['schematic_parity']
 assert state['new_layout_and_route_executed_after_contract_change'] is False
 print('PASS: 17 vendor source files and migration payload hashes preserved.')
 print('WIP: AM200 PCB has 22 DRC violations / 11 unconnected; contract/PCB dimensions differ.')
 print('This check is NOT a new-board ERC/DRC, firmware build, assembly or production release.')

if __name__=='__main__':main()

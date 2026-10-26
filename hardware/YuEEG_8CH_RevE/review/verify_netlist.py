"""Verify KiCad's exported connectivity, not just generated source text."""
from pathlib import Path
import json, csv, xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
tree=ET.parse(root/'review/netlist.xml')
comps={c.get('ref'):c for c in tree.findall('./components/comp')}
expected=json.loads((root/'review/expected_connections.json').read_text())
actual={}
for net in tree.findall('./nets/net'):
    for node in net.findall('node'):
        key=node.get('ref')+'.'+node.get('pin')
        assert key not in actual, ('Pin appears in multiple nets',key)
        actual[key]=net.get('name')
failures=[]
for key,want in expected.items():
    if key.startswith('#'):continue # PWR_FLAG is intentionally absent from PCB netlist.
    got=actual.get(key,'')
    if want is None:
        if got and not got.startswith('unconnected-'):
            failures.append((key,'explicit NC',got))
    elif got.rsplit('/',1)[-1]!=want:
        failures.append((key,want,got))
with (root/'BOM.csv').open(encoding='utf-8-sig') as f:
    bom={row['Reference']:row for row in csv.DictReader(f)}
assert set(comps)==set(bom), ('BOM/netlist mismatch',set(comps)^set(bom))
assert {k for k in actual if k.startswith('U1.')}=={f'U1.{i}' for i in range(1,65)}
assert not failures, failures
report={'components':len(comps),'sheets':len(tree.findall('./design/sheet')),
        'exported_pins':len(actual),'ADS1299_pins':64,
        'connected_pins_checked':sum(v is not None and not k.startswith('#') for k,v in expected.items()),
        'explicit_NC_pins_checked':sum(v is None for v in expected.values()),
        'connection_mismatches':len(failures),
        'scope':'KiCad netlist vs intended connectivity; not analog simulation, PCB validation or safety certification'}
(root/'review/connectivity_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))

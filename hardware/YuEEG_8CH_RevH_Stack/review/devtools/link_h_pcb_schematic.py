from pathlib import Path
import sys,json,csv,xml.etree.ElementTree as E
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack')
for board in ['afe','digital','power']:
 base=R/board;stem='YuEEG_H_'+board.upper();path=base/(stem+'.kicad_pcb');d=loads(path.read_text());root=loads((base/(stem+'.kicad_sch')).read_text());rootid=json.loads(sub(root,'uuid')[1])
 comps={c.get('ref'):c for c in E.parse(base/'review/netlist.xml').findall('./components/comp')};bom={r['Reference']:r for r in csv.DictReader((base/'BOM.csv').open(encoding='utf-8-sig'))};actual={};seen=set()
 for f in d:
  if not isinstance(f,list) or f[0]!='footprint':continue
  props={json.loads(x[1]):x for x in f if isinstance(x,list) and x[0]=='property'};ref=json.loads(props['Reference'][2])
  if 'board_only' in (sub(f,'attr') or []):
   assert 'exclude_from_bom' in sub(f,'attr') and 'exclude_from_pos_files' in sub(f,'attr')
   pads=[q for q in f if isinstance(q,list) and q[0]=='pad']
   if pads:
    assert all(json.loads(q[1])=='' and q[2]=='np_thru_hole' and not sub(q,'net') for q in pads),(ref,'Only explicitly non-electrical NPTH features may be skipped')
   else:
    assert json.loads(f[1])=='YuEEG:MountingHole_M2_Routed_2p4'
    cuts=[q for q in f if isinstance(q,list) and q[0]=='fp_circle' and sub(q,'layer')[1]=='"Edge.Cuts"']
    assert len(cuts)==1 and sub(cuts[0],'center')[1:]==['0','0'] and sub(cuts[0],'end')[1:]==['1.2','0']
    assert not any(isinstance(q,list) and q[0] in ['zone','pad'] for q in f)
    assert all(json.loads(sub(q,'layer')[1]) in ['F.SilkS','B.SilkS','F.Fab','B.Fab','F.CrtYd','B.CrtYd','Cmts.User','Dwgs.User','Edge.Cuts'] for q in f if isinstance(q,list) and q[0].startswith('fp_') and sub(q,'layer'))
   continue
  seen.add(ref);row=bom[ref];c=comps[ref]
  f[1]=json.dumps(row['Footprint']);props['Value'][2]=json.dumps(row['Value'])
  sp=c.find('sheetpath').get('tstamps');symbol=c.findtext('tstamps').split()[0];value='/'+rootid+sp+symbol
  old=sub(f,'path')
  if old:old[1]=json.dumps(value)
  else:f.append(['path',json.dumps(value)])
  for pad in f:
   if not isinstance(pad,list) or pad[0]!='pad':continue
   number=json.loads(pad[1]);net=sub(pad,'net');name=json.loads(net[2]) if net and len(net)>2 else ''
   if number:actual[ref+'.'+number]=name
 assert seen==set(bom),(board,seen^set(bom))
 expected=json.loads((base/'review/expected_connections.json').read_text());fail=[]
 for pin,net in expected.items():
  if pin.startswith('#'):continue
  a=actual.get(pin)
  if net is None:
   if a and not a.startswith('unconnected-'):fail.append([pin,net,a])
  elif a!=net:fail.append([pin,net,a])
 assert not fail,fail
 path.write_text(dumps(d));(base/'review/pcb_pin_contract.json').write_text(json.dumps({'components_checked':len(seen),'pins_checked':len([q for q in expected if not q.startswith('#')]),'mismatches':0,'scope':'Raw PCB pad numbers/netnames versus exported expected contract; source instance paths and footprint IDs linked. Copper routing and functional performance are separate checks.'},indent=2))
 print(board,'linked schematic instances; PCB pad net contract passed')

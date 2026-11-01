"""Build a separate, explicitly remapped AM200 FPC; never overwrite the AM178 link.

Reuse the in-repository schematic/layout/router implementations with named paths
and distinct endpoint contracts. Run stages sequentially: schematic, layout, route,
finish. The user-supplied vendor files are reference data, never executed.
"""
from pathlib import Path
import argparse, json, hashlib, shutil, sys, subprocess

H = Path('hardware/YuEEG_8CH_RevH_Stack')
D = H / 'display_am200'
DEV = H / 'review/devtools'
STEM = 'YuEEG_H_AM200_LINK'
panel = {
 '1':'VCI_EN', '2':'AM_D3_P', '3':'AM_D2_P', '4':'AM_D1_P',
 '5':'AM_D0_P', '6':'AM_CLK_P', '7':'AM_CS_P', '8':'AM_RST_P',
 '9':None, '10':'GND', '11':None, '12':None, '13':None,
 '14':'AM_1V8', '15':'AM_RAW', '16':'GND', '17':None,
 '18':'GND', '19':None, '20':None, '21':'GND',
 '22':'AM_RAW', '23':'AM_RAW', '24':None,
 '25':'GND', '26':'GND', '27':'GND', '28':'GND',
}
ap = argparse.ArgumentParser()
ap.add_argument('stage', choices=['schematic','layout','route','finish'])
args = ap.parse_args()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def source(name):
 s = (DEV / name).read_text(encoding='utf8')
 s = s.replace("H/'display_link'", "H/'display_am200'")
 s = s.replace("RevH_Stack/display_link", "RevH_Stack/display_am200")
 s = s.replace('YuEEG_H_DISPLAY_LINK', STEM)
 s = s.replace('hardware/YuEEG_8CH_RevA/review/build_schematic.py',
               'tools/legacy_build_support/schematic_helpers.py')
 return s

if args.stage == 'schematic':
 s = source('build_h_display_link.py')
 s = s.replace('straight=1.85;', 'straight=2.85;')
 s = s.replace("male='OCN_", "pins['19']=None; pins['20']=None\nendpoint_pins={'JF1':pins, 'JF2':panel}\nmale='OCN_", 1)
 s = s.replace('x,121.92,pins,footprint=', 'x,121.92,endpoint_pins[ref],footprint=')
 s = s.replace('Passive extension / same logical pin at both ends',
               'AM200 PIN REMAP / NOT A STRAIGHT THROUGH CABLE')
 s = s.replace('DISPLAY FPC EXTENSION / PROTOTYPE / NOT FOR ORDER',
               'REV H TO AM200Q460460LK / REMAPPED / NOT FOR ORDER')
 s = s.replace('OK-14GM024-04 / MAIN', 'OK-14GM024-04 / REV H INPUT')
 s = s.replace('OK-14F024-04 / SCREEN', 'OK-14F024-04 / AM200 OUTPUT')
 assert 'endpoint_pins[ref]' in s
 exec(compile(s, str(DEV/'build_h_display_link.py'), 'exec'), globals())
 qpath = D/'review/design_contract.json'
 q = json.loads(qpath.read_text())
 previous = json.loads((H/'display_link/review/design_contract.json').read_text())
 q.update(panel='AM200Q460460LK', status='AM200_REMAP_ENGINEERING_NOT_FOR_ORDER',
          pins_by_connector=endpoint_pins,
          end_taper_offsets_by_connector_mm=previous['end_taper_offsets_by_connector_mm'],
          scope='JF1 mates to unchanged Rev H J2002 legacy electrical pinout; JF2 is AM200Q460460LK. Never use the old straight-through AM178 link. Display only; CST820 reset held low and no MCU touch bus. Pin13 is NC per interface table and official adapter schematic; drawing label differs.',
          procurement='User specifies OCN/亚奇 OK-14F024-04 0.4mm female socket. Matching original panel male is shown in vendor drawing. Actual delivered pair and contact numbering require sample verification.')
 qpath.write_text(json.dumps(q, indent=2))
 pro = json.loads((H/'display_link/YuEEG_H_DISPLAY_LINK.kicad_pro').read_text())
 (D/(STEM+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
 shutil.copy2(H/'display_link/YuEEG_H_DISPLAY_LINK.kicad_dru',D/(STEM+'.kicad_dru'))
elif args.stage == 'layout':
 s = source('layout_h_display_link.py')
 s = s.replace("q['pins'][pad.GetNumber()]", "q['pins_by_connector'][ref][pad.GetNumber()]")
 s = s.replace('OK-14GM024-04 / MAIN', 'OK-14GM024-04 / REV H INPUT')
 s = s.replace('OK-14F024-04 / SCREEN', 'OK-14F024-04 / AM200 OUTPUT')
 exec(compile(s,str(DEV/'layout_h_display_link.py'),'exec'),globals())
elif args.stage == 'route':
 # The original Rev F router is not part of the frozen public delivery.
 import types
 helper=types.ModuleType('h_local_router')
 hs=(DEV/'h_local_router.py').read_text(encoding='utf8').replace(
  'hardware/YuEEG_8CH_RevF/review/local_router_f.py',
  'tools/legacy_build_support/local_router_f.py')
 exec(compile(hs,str(DEV/'h_local_router.py'),'exec'),helper.__dict__)
 sys.modules['h_local_router']=helper
 s=source('route_h_display_link.py')
 s=s.replace('[6.35,5.15,4.75,3.95,4.35,5.95,5.55]',
             '[6.35,5.15,4.75,3.95,4.35,5.95,5.55]')
 s=s.replace('[2.05,2.35,2.75,4.35,4.75,6.35]',
             '[2.06,2.35,2.75,4.35,4.75,6.35]')
 s=s.replace("[('JF1',left),('JF2',right)]", "[('JF2',right),('JF1',left)]")
 s=s.replace("'TP_SDA_IDLE','TP_SCL_IDLE',", '')
 s=s.replace("'TP_SDA_IDLE','TP_SCL_IDLE'", '')
 s=s.replace('[2.06,2.35,2.75,4.35,4.75,6.35]', '[2.06,2.35,2.75,6.35]')
 fanout='''
fanouts={}
for f in b.GetFootprints():
 cx,cy=loc(f.GetPosition())
 for v in f.Pads():
  net=v.GetNetname()
  if net not in high+['VCI_EN','AM_1V8','AM_RAW']:continue
  x,y=loc(v.GetPosition());col=round((x-1.8)/.4)
  vy=cy+(1 if y>cy else -1)*(.23 if col%2 else .45)
  t=p.PCB_TRACK(b);t.SetStart(v.GetPosition());t.SetEnd(p.VECTOR2I(p.FromMM(x),p.FromMM(vy)));t.SetWidth(p.FromMM(.1));t.SetLayer(p.B_Cu);t.SetNet(v.GetNet());b.Add(t)
  via=p.PCB_VIA(b);via.SetPosition(t.GetEnd());via.SetWidth(p.FromMM(.3));via.SetDrill(p.FromMM(.1));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(v.GetNet());b.Add(via)
  fanouts[f.GetReference()+'.'+v.GetNumber()]=(x,vy)
'''
 s=s.replace("save()\nfor net in high",fanout+"\nsave()\nfor net in high",1)
 s=s.replace("start=loc(v.GetPosition());targets=", "start=fanouts.get(ref+'.'+v.GetNumber(),loc(v.GetPosition()));targets=")
 s=s.replace('width=.15 if net', 'width=.15 if net')
 s=s.replace('sl=1,el=el)', "sl=0 if ref+'.'+v.GetNumber() in fanouts else 1,el=el)")
 exec(compile(s,str(DEV/'route_h_display_link.py'),'exec'),globals())
else:
 import pcbnew as p, wx
 wx.DisableAsserts()
 sys.path.insert(0,str(Path('hardware/YuEEG_8CH_RevG/review').resolve()))
 from sexpr_io import loads,dumps,sub
 f = D/(STEM+'.kicad_pcb')
 tree = loads(f.read_text())
 old = loads((H/'display_link/YuEEG_H_DISPLAY_LINK.kicad_pcb').read_text())
 for v in tree:
  if isinstance(v,list) and v[0]=='gr_rect' and sub(v,'layer')[1]=='"F.Adhes"':
   sub(sub(v,'stroke'),'width')[1]='0';sub(v,'fill')[1]='solid'
 b = p.LoadBoard(str(f)); code = str(b.FindNet('GND').GetNetCode())
 for v in old:
  if not isinstance(v,list): continue
  if v[0]=='gr_text':
   v[1]=v[1].replace('DISPLAY','AM200 DISPLAY')
   tree.append(v)
 f.write_text(dumps(tree))
 s=source('fill_h_display_link_ground.py').replace('SetLocalClearance(p.FromMM(.1))','SetLocalClearance(p.FromMM(.15))')
 exec(compile(s,str(DEV/'fill_h_display_link_ground.py'),'exec'),globals())
 project=D/(STEM+'.kicad_pro'); saved=project.read_bytes()
 b=p.LoadBoard(str(f)); p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(f),b)
 project.write_bytes(saved)
 print('AM200 FPC copper refilled; native checks must be run separately.')

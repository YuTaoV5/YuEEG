from pathlib import Path
import pcbnew as p,wx,json,uuid,sys,xml.etree.ElementTree as E
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'display_link';stem='YuEEG_H_DISPLAY_LINK';project=D/(stem+'.kicad_pro');project_bytes=project.read_bytes();q=json.loads((D/'review/design_contract.json').read_text());W,B=q['outline_mm'];b=p.BOARD();b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(p.FromMM(q['finished_fpc_thickness_mm']));nets={};xmlnets={n.get('ref')+'.'+n.get('pin'):net.get('name') for net in E.parse(D/'review/netlist.xml').findall('./nets/net') for n in net.findall('node')}
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for ref,name in [('JF1','OCN_OK_14GM024_04_LogicalMate'),('JF2','OCN_OK_14F024_04_GangMask')]:
 f=p.FootprintLoad(str(D/'footprints/YuEEG_Display.pretty'),name);assert f;b.Add(f);f.SetReference(ref);f.SetValue('OK-14GM024-04 / MAIN' if ref=='JF1' else 'OK-14F024-04 / SCREEN');f.SetFPID(p.LIB_ID('YuEEG_Display',name));f.Flip(f.GetPosition(),False);f.SetOrientationDegrees(q['B_side_rotations_deg'][ref]);f.SetPosition(xy(*q['connector_centers_flat_mm'][ref]));f.Reference().SetVisible(False);f.Value().SetVisible(False)
 for pad in f.Pads():
  net=q['pins'][pad.GetNumber()] or xmlnets[ref+'.'+pad.GetNumber()]
  if net not in nets:n=p.NETINFO_ITEM(b,net);b.Add(n);nets[net]=n
  pad.SetNet(nets[net])
my=q['connector_centers_flat_mm']['JF1'][1];fy=q['connector_centers_flat_mm']['JF2'][1];lo=(W-q['neck_width_mm'])/2;hi=W-lo
outline=[(0,0),(W,0),(W,my+1.8),(hi,my+2.3),(hi,fy-2.3),(W,fy-1.8),(W,B),(0,B),(0,fy-1.8),(lo,fy-2.3),(lo,my+2.3),(0,my+1.8),(0,0)]
for a,c in zip(outline,outline[1:]):
 g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(xy(*a));g.SetEnd(xy(*c));g.SetLayer(p.Edge_Cuts);g.SetWidth(p.FromMM(.05));b.Add(g)
path=D/(stem+'.kicad_pcb');p.SaveBoard(str(path),b);project.write_bytes(project_bytes)
sys.path.insert(0,str(Path('hardware/YuEEG_8CH_RevG/review').resolve()));from sexpr_io import loads,dumps,sub
tree=loads(path.read_text());root=json.loads(sub(loads((D/(stem+'.kicad_sch')).read_text()),'uuid')[1]);comps={c.get('ref'):c for c in E.parse(D/'review/netlist.xml').findall('./components/comp')}
for f in tree:
 if not(isinstance(f,list) and f[0]=='footprint'):continue
 ref=next(json.loads(t[2]) for t in f if isinstance(t,list) and t[:2]==['property','"Reference"']);c=comps[ref];f.append(['path',json.dumps('/'+root+c.find('sheetpath').get('tstamps')+c.findtext('tstamps').split()[0])])
a,c=q['bend_interval_flat_y_mm'];tree.append(['zone',['net','0'],['net_name','""'],['layers','"F.Cu"','"B.Cu"'],['uuid',json.dumps(str(uuid.uuid4()))],['name','"STATIC_BEND_NO_VIAS_OR_PADS"'],['hatch','edge','.5'],['connect_pads',['clearance','0']],['min_thickness','.1'],['filled_areas_thickness','no'],['keepout',['tracks','allowed'],['vias','not_allowed'],['pads','not_allowed'],['copperpour','allowed'],['footprints','not_allowed']],['fill',['thermal_gap','.2'],['thermal_bridge_width','.2']],['polygon',['pts',['xy','0',str(a-.15)],['xy',str(W),str(a-.15)],['xy',str(W),str(c+.15)],['xy','0',str(c+.15)]]]])
for y1,y2 in [(my-1.5,my+1.5),(fy-1.5,fy+1.5)]:tree.append(['gr_rect',['start','.2',str(y1)],['end',str(W-.2),str(y2)],['stroke',['width','.1'],['type','default']],['fill','none'],['layer','"F.Adhes"'],['uuid',json.dumps(str(uuid.uuid4()))]])
path.write_text(dumps(tree));print('Two B-side connectors and bend/stiffener regions placed; not routed')


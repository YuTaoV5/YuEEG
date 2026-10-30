from pathlib import Path
import pcbnew as p,wx,json,sys,uuid,copy
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');lib=R/'footprints/YuEEG.pretty/ALPS_SKRTLBE010_GroundedShell.kicad_mod';d=loads(lib.read_text());d[:]=[z for z in d if not(isinstance(z,list) and z[0]=='zone')]
z=['zone',['net','0'],['net_name','""'],['layer','"F.Cu"'],['uuid',json.dumps(str(uuid.uuid4()))],['name','"ALPS_UNDERBODY_NO_COPPER"'],['hatch','edge','.5'],['connect_pads',['clearance','0']],['min_thickness','.15'],['filled_areas_thickness','no'],['keepout',['tracks','not_allowed'],['vias','not_allowed'],['pads','allowed'],['copperpour','not_allowed'],['footprints','allowed']],['fill',['thermal_gap','.3'],['thermal_bridge_width','.3']],['polygon',['pts',*(['xy',str(x),str(y)] for x,y in [(-1.05,.25),(1.05,.25),(1.05,1.55),(-1.05,1.55)])]]]
d.append(z);lib.write_text(dumps(d));path=R/'digital/YuEEG_H_DIGITAL.kicad_pcb';board=p.LoadBoard(str(path));tree=loads(path.read_text());allnets={json.loads(n[2]):n[1] for n in tree if isinstance(n,list) and n[0]=='net'};evidence=[]
def prop(n,key):return next(z for z in n if isinstance(z,list) and z[:2]==['property',json.dumps(key)])
for ref in ['SW301','SW302','SW1001']:
 old=next(f for f in board.GetFootprints() if f.GetReference()==ref);mapping={q.GetNumber():q.GetNetname() for q in old.Pads()};temp=p.BOARD();f=p.FootprintLoad(str(lib.parent),lib.stem);temp.Add(f);f.SetPosition(old.GetPosition());f.SetOrientationDegrees(old.GetOrientationDegrees());f.SetReference(ref);f.SetValue(old.GetValue());f.Reference().SetLayer(p.F_Fab);f.Value().SetLayer(p.F_Fab)
 nets={}
 for net in set(mapping.values()):n=p.NETINFO_ITEM(temp,net);temp.Add(n);nets[net]=n
 for q in f.Pads():q.SetNet(nets[mapping[q.GetNumber()]])
 tmp=Path('logs/switch_keepout_exchange.kicad_pcb');p.SaveBoard(str(tmp),temp);new=next(v for v in loads(tmp.read_text()) if isinstance(v,list) and v[0]=='footprint');new[1]='"YuEEG:ALPS_SKRTLBE010_GroundedShell"';oldraw=next(v for v in tree if isinstance(v,list) and v[0]=='footprint' and prop(v,'Reference')[2]==json.dumps(ref))
 for q in new:
  if isinstance(q,list) and q[0]=='pad':sub(q,'net')[1]=allnets[json.loads(sub(q,'net')[2])]
 if sub(oldraw,'path'):new.append(copy.deepcopy(sub(oldraw,'path')))
 tree[tree.index(oldraw)]=new;evidence.append({'reference':ref,'keepout_polygons_global_mm':[[[p.ToMM(zone.Outline().COutline(0).CPoint(i).x),p.ToMM(zone.Outline().COutline(0).CPoint(i).y)] for i in range(zone.Outline().COutline(0).PointCount())] for zone in f.Zones()]})
path.write_text(dumps(tree));(R/'digital/review/switch_keepout_review.json').write_text(json.dumps({'source':'https://tech.alpsalpine.com/cms.media/product_detail_fig_skrt_d_22_en_3a47b185ac.gif','source_circuit':'https://tech.alpsalpine.com/cms.media/product_detail_fig_skrt_d_3_en_07d94ff9ef.gif','local_prohibition_mm':[-1.05,.25,1.05,1.55],'basis':'Manufacturer 2x1.2mm hatched copper-prohibited area with 0.05mm extra margin. Mounting surface copper/tracks/vias prohibited; inner planes unaffected. Pins 1/3 common mapped to logical key pin1; pin2 and shell mapped GND.','instances':evidence},indent=2));print('Three side-key footprints now contain native mounting-surface copper keepouts')

"""Round nonmetal mounting openings; retain the complete electrical keepout."""
from pathlib import Path
import sys,json,copy,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');name='MountingHole_M2_Routed_2p4';lib=loads((R/'footprints/MountingHole.pretty/MountingHole_2.2mm_M2.kicad_mod').read_text());lib[1]=json.dumps(name)
lib[:]=[n for n in lib if not(isinstance(n,list) and n[0]=='pad')]
lib.append(['fp_circle',['center','0','0'],['end','1.2','0'],['stroke',['width','.05'],['type','default']],['fill','none'],['layer','"Edge.Cuts"']])
(R/'footprints/YuEEG.pretty'/(name+'.kicad_mod')).write_text(dumps(lib))
for board in ['afe','digital']:
 path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');d=loads(path.read_text())
 for f in d:
  if not(isinstance(f,list) and f[0]=='footprint' and 'board_only' in (sub(f,'attr') or [])):continue
  ref=next(json.loads(q[2]) for q in f if isinstance(q,list) and q[0]=='property' and q[1]=='"Reference"');assert ref in ['H1','H2','H3']
  f[1]=json.dumps('YuEEG:'+name);f[:]=[n for n in f if not(isinstance(n,list) and n[0]=='pad')]
  f.append(copy.deepcopy(lib[-1]))
 path.write_text(dumps(d));b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
data=json.loads((R/'review/mounting_holes.json').read_text())
for q in data['features']:q.pop('finished_NPTH_mm',None);q['finished_unplated_opening_mm']=2.4;q['representation']='Edge.Cuts internal circles; not duplicated in Excellon drill files'
data['status']='Native 2.4mm internal cutouts for M2 insulating fasteners; full pad/track/via/pour exclusions retained. Manufacturing must process all three internal circles in Edge.Cuts. Mechanical assembly and material qualification remain pending.'
data['manufacturing_source']='https://jlcpcb.com/capabilities/pcb-capabilities/'
(R/'review/mounting_holes.json').write_text(json.dumps(data,indent=2));print('Three M2 internal openings per board now in Edge.Cuts; copper exclusions unchanged')

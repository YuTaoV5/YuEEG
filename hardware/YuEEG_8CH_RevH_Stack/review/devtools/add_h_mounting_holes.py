from pathlib import Path
import pcbnew as p,wx,json,shutil,sys
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');coords=[(44,4),(44,51),(4,55)];fpname='MountingHole_2.2mm_M2';lib=Path('X:/SoftWare/Kicad/share/kicad/footprints/MountingHole.pretty');dest=R/'footprints/MountingHole.pretty';dest.mkdir(exist_ok=True);shutil.copy2(lib/(fpname+'.kicad_mod'),dest/(fpname+'.kicad_mod'));records=[]
for board in ['afe','digital']:
 path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');b=p.LoadBoard(str(path));assert not any(f.GetReference() in ['H1','H2','H3'] for f in b.GetFootprints())
 backup=R/'archive/before_mount_holes'/board;backup.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup/path.name)
 for i,pos in enumerate(coords,1):
  f=p.FootprintLoad(str(dest),fpname);b.Add(f);f.SetReference('H'+str(i));f.SetValue('M2 NYLON ONLY');f.SetPosition(p.VECTOR2I(*[p.FromMM(v) for v in pos]));f.SetAttributes(f.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES);f.Reference().SetVisible(False);f.Value().SetVisible(False)
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
 d=loads(path.read_text())
 for f in d:
  if isinstance(f,list) and f[0]=='footprint' and next(json.loads(q[2]) for q in f if isinstance(q,list) and q[0]=='property' and q[1]=='"Reference"') in ['H1','H2','H3']:f[1]=json.dumps('MountingHole:'+fpname)
 path.write_text(dumps(d));records.append({'board':board,'positions_mm':coords,'finished_NPTH_mm':2.2})
(R/'review/mounting_holes.json').write_text(json.dumps({'features':records,'hardware_constraint':'All screws, washers and spacers must be insulating; no metal inserts or metal through-bolts across the boards.','nominal_AFE_to_digital_surface_gap_mm':8.5,'spacer_option':'M2 8mm insulating spacer plus .5mm insulating washer as nominal dimensional option; exact part, tolerance and assembly remain to be qualified.','status':'Native nonplated drill features added; DRC and connector insertion checks must be rerun. This is not a complete enclosure or safety approval.'},indent=2));print('Added three coaxial NPTH mounting holes to AFE and digital boards')

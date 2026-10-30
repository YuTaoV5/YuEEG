"""Logical column/row fold alignment and bend copper checks, not physical mating."""
from pathlib import Path
import pcbnew as p,json,math,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'display_link';path=D/'YuEEG_H_DISPLAY_LINK.kicad_pcb';q=json.loads((D/'review/design_contract.json').read_text());b=p.LoadBoard(str(path));main=p.LoadBoard(str(H/'digital/YuEEG_H_DIGITAL.kicad_pcb'));mf=next(f for f in main.GetFootprints() if f.GetReference()=='J2002');fs={f.GetReference():f for f in b.GetFootprints()};assert mf.GetOrientationDegrees()==0
def pos(x):return [p.ToMM(x.x),p.ToMM(x.y)]
mx,my=pos(mf.GetPosition());cols=[];upper=[];lp={v.GetNumber():v for v in fs['JF1'].Pads()};up={v.GetNumber():v for v in fs['JF2'].Pads()};mp={v.GetNumber():v for v in mf.Pads()};lx,ly=pos(fs['JF1'].GetPosition());ux,uy=pos(fs['JF2'].GetPosition())
for n,v in mp.items():
 target=pos(v.GetPosition());source=pos(up[n].GetPosition());folded=[mx+source[0]-ux,my-(source[1]-uy)];upper.append({'pin':n,'error_mm':math.dist(folded,target)})
 if int(n)<=24:
  source=pos(lp[n].GetPosition());relative=[source[0]-lx,source[1]-ly];targetrel=[target[0]-mx,target[1]-my];cols.append({'pin':n,'column_error_mm':abs(relative[0]-targetrel[0]),'same_row_side':relative[1]*targetrel[1]>0})
a,c=q['bend_interval_flat_y_mm'];bad_vias=[];bad_tracks=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  x,y=pos(t.GetPosition())
  if a<=y<=c:bad_vias.append([x,y,t.GetNetname()])
 else:
  s,e=pos(t.GetStart()),pos(t.GetEnd())
  if max(s[1],e[1])>a+1e-5 and min(s[1],e[1])<c-1e-5 and abs(s[0]-e[0])>1e-5:bad_tracks.append({'net':t.GetNetname(),'start':s,'end':e})
record={'status':'PROTOTYPE_GEOMETRIC_CHECK_NOT_MATING_OR_ASSEMBLY_RELEASE','pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'main_pcb_sha256':hashlib.sha256((H/'digital/YuEEG_H_DIGITAL.kicad_pcb').read_bytes()).hexdigest(),'upper_socket_folded_pad_checks':upper,'lower_header_signal_column_and_row_checks':cols,'bend_vias':bad_vias,'nonparallel_tracks_in_bend':bad_tracks,'bend_radius_neutral_mm':q['U_fold_neutral_radius_mm'],'inner_radius_at_nominal_thickness_mm':q['U_fold_neutral_radius_mm']-q['finished_fpc_thickness_mm']/2,'max_fpc_thickness_for_inner_radius_ge_10t_mm':q['U_fold_neutral_radius_mm']/10.5,'scope':'Fold transforms verify project logical columns and row sides only. Male/female PCB land row offsets differ by design. Connector internal contacts, real pin-1 marking, solder fillets, screen-back datum, exact stiffener/fabricator stack and assembled continuity are not proved.'}
(D/'review/fold_alignment.json').write_text(json.dumps(record,indent=2));print('Upper max error',max(v['error_mm'] for v in upper),'mm; lower bad columns',sum(v['column_error_mm']>1e-5 or not v['same_row_side'] for v in cols),'bend vias',len(bad_vias),'nonparallel bend segments',len(bad_tracks));assert max(v['error_mm'] for v in upper)<1e-5 and all(v['column_error_mm']<1e-5 and v['same_row_side'] for v in cols) and not bad_vias and not bad_tracks

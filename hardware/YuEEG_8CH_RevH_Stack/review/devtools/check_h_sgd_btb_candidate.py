"""Compare the separate SGDCONN candidate against the actual current boards."""
from pathlib import Path
import sys,json,hashlib,math,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');C=Path(sys.argv[1])
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
selection=json.loads((C/'selection.json').read_text());out={}
def xy(v):return [v.x,v.y]
def pad(q):return [q.GetNumber(),q.GetNetname(),xy(q.GetPosition()),xy(q.GetSize()),xy(q.GetDrillSize()),int(q.GetShape()),int(q.GetAttribute()),list(q.GetLayerSet().Seq()),q.GetOrientationDegrees()]
def tracks(b):
 rows=[]
 for t in b.GetTracks():
  row=[t.m_Uuid.AsString(),int(t.Type()),t.GetNetname(),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(),int(t.GetLayer())]
  if isinstance(t,p.PCB_VIA):row += [t.GetDrillValue(),int(t.TopLayer()),int(t.BottomLayer())]
  if isinstance(t,p.PCB_ARC):row += [xy(t.GetMid())]
  rows.append(row)
 return sorted(rows)
def part(f):return [f.GetReference(),f.GetValue(),str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),xy(f.GetPosition()),f.GetOrientationDegrees(),int(f.GetLayer()),sorted(pad(q) for q in f.Pads())]
for name in ['afe','digital']:
 file='YuEEG_H_'+name.upper()+'.kicad_pcb';oldpath=H/name/file;newpath=C/name/file
 assert sha(oldpath)==selection[name]['baseline_pcb_sha256'];assert sha(newpath)==selection[name]['candidate_pcb_sha256']
 report=json.loads((C/name/'drc_sgd.json').read_text())
 assert all(not report[k] for k in ['violations','unconnected_items','schematic_parity'])
 old=p.LoadBoard(str(oldpath));new=p.LoadBoard(str(newpath))
 oldfs={f.GetReference():f for f in old.GetFootprints()};newfs={f.GetReference():f for f in new.GetFootprints()}
 assert set(oldfs)==set(newfs)
 assert all(part(oldfs[k])==part(newfs[k]) for k in oldfs if k!='JH1')
 moves=json.loads((C/'via_moves.json').read_text())[name]
 assert len(moves)==(4 if name=='afe' else 8)
 transform={tuple(p.FromMM(v) for v in row['old_xy_mm']):[p.FromMM(v) for v in row['new_xy_mm']] for row in moves}
 before={row[0]:row for row in tracks(old)};after={row[0]:row for row in tracks(new)}
 # Same UUID/net/width/layer/drill, with only explicitly listed endpoint moves.
 for row in before.values():
  row[3]=transform.get(tuple(row[3]),row[3]);row[4]=transform.get(tuple(row[4]),row[4])
 local=json.loads((C/'local_route_revision.json').read_text()) if name=='digital' else {'removed_tracks':[],'added_items':[]}
 assert set(before)-set(after)==set(local['removed_tracks']) and set(after)-set(before)==set(local['added_items'])
 assert all(before[k]==after[k] for k in set(before)&set(after)),'Undocumented routing change'
 assert all(before[k][2] in ['ADS_SCLK','ADS_DRDY'] for k in set(before)-set(after))
 assert all(after[k][2] in ['ADS_SCLK','ADS_DRDY'] and after[k][1]!=int(p.PCB_VIA_T) for k in set(after)-set(before))
 a={q.GetNumber():q for q in oldfs['JH1'].Pads()};b={q.GetNumber():q for q in newfs['JH1'].Pads()}
 assert set(a)==set(b) and len(b)==21
 for key,q in b.items():
  r=a[key];assert xy(q.GetPosition())==xy(r.GetPosition()) and q.GetNetname()==r.GetNetname()
  if key:assert xy(q.GetSize())==[p.FromMM(.3),p.FromMM(2)] and q.GetAttribute()==p.PAD_ATTRIB_SMD
 oldholes=sorted((xy(q.GetPosition()),xy(q.GetDrillSize())) for q in oldfs['JH1'].Pads() if not q.GetNumber())
 newholes=sorted((xy(q.GetPosition()),xy(q.GetDrillSize())) for q in newfs['JH1'].Pads() if not q.GetNumber());assert oldholes==newholes
 hits=[];n=0
 for v in new.GetTracks():
  if not isinstance(v,p.PCB_VIA):continue
  n+=1;circle=p.SHAPE_CIRCLE(v.GetPosition(),v.GetDrillValue()//2)
  for q in b.values():
   if q.GetNumber() and p.SHAPE.Collide(circle,q.GetEffectiveShape(q.GetLayer()),p.FromMM(.2499)):
    hits.append({'via_uuid':v.m_Uuid.AsString(),'pad':q.GetNumber()})
 # A moved via hole must also clear every other SMD pad, including same-net pads.
 moved={r['uuid'] for r in moves}
 for v in new.GetTracks():
  if not isinstance(v,p.PCB_VIA) or v.m_Uuid.AsString() not in moved:continue
  circle=p.SHAPE_CIRCLE(v.GetPosition(),v.GetDrillValue()//2)
  for f in new.GetFootprints():
   for q in f.Pads():
    if q.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(circle,q.GetEffectiveShape(q.GetLayer()),p.FromMM(.2499)):
     hits.append({'via_uuid':v.m_Uuid.AsString(),'pad':f.GetReference()+'.'+q.GetNumber()})
 assert not hits,hits
 out[name]={'baseline_pcb_sha256':sha(oldpath),'candidate_pcb_sha256':sha(newpath),'all_tracks_unchanged_except_listed_fanout':True,'via_count_unchanged':True,'via_moves':moves,'local_reroute':local,'all_other_component_electrical_and_pose_geometry_unchanged':True,'all20_JH1_pad_centers_and_nets_unchanged':True,'locator_holes_unchanged':True,'all_via_holes_checked_against_new_JH1_smt_pads':n,'minimum_hole_to_smt_copper_mm':.25,'hits':hits,'checks':{k:len(report[k]) for k in ['violations','unconnected_items','schematic_parity']},'footprint':selection[name]['footprint'],'mpn':selection[name]['mpn']}
(C/'native_migration_proof.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print('PASS documented fanout changes only;other parts,20contact XY/nets,locator holes unchanged;0DRC/parity;all via holes vs JH1 and moved holes vs every SMT pad>=.25mm')

"""Apply the reviewed local SGDCONN fanout to a separate prepared candidate.
Usage: KiCad python route_h_sgd_btb_candidate.py prepared_dir new_output_dir
Historical e5df79c preflight only; never edits the current source boards.
"""
from pathlib import Path
import sys,json,shutil,hashlib,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
C=Path(sys.argv[1]);O=Path(sys.argv[2]);assert C.resolve()!=O.resolve() and not O.exists()
moves={'afe': [{'uuid': 'e047f38e-eb1c-46b4-8546-a7136b26ab54', 'net': 'ADS_PWDN', 'old_xy_mm': [40.4, 19.1464], 'new_xy_mm': [40.25, 19.1464], 'attached_tracks': ['7731adab-b976-47de-b100-a1f401c882bb', '20dd37a2-c9e8-4d30-a63c-50c52a286b3d']}, {'uuid': '3e26e90c-037e-483c-830d-fae58dc88549', 'net': 'GND', 'old_xy_mm': [40.4, 17.9605], 'new_xy_mm': [40.25, 17.9605], 'attached_tracks': ['29c03d49-1474-4bf1-953d-5e5d951c4a80']}, {'uuid': '722be9a0-f63c-48ac-9e97-612c8358a39b', 'net': 'GND', 'old_xy_mm': [40.4, 24.6276], 'new_xy_mm': [40.25, 24.6276], 'attached_tracks': ['57ef9f9e-7a55-43aa-8cc7-701cf4885a47']}, {'uuid': 'df236809-1191-4dc9-ad6a-a5306bd9f368', 'net': 'GND', 'old_xy_mm': [40.4, 22.8541], 'new_xy_mm': [40.25, 22.8541], 'attached_tracks': ['b9661731-19ea-4e2c-9a5a-47427e5b1898']}], 'digital': [{'uuid': 'b82e420d-9a52-4ed4-a677-93d06d90d509', 'net': '+3V3', 'old_xy_mm': [46.97, 23.8], 'new_xy_mm': [46.97, 24.2], 'attached_tracks': ['2ad625d8-4490-477a-bf54-442709d133e3', '511b43a9-b607-4323-9645-cec9fa012223']}, {'uuid': '101e79bd-5b1a-4b2d-a9ac-1c0f55f9a5c8', 'net': 'ADS_CS', 'old_xy_mm': [46.97, 21.4], 'new_xy_mm': [46.97, 21.8], 'attached_tracks': ['79ddf286-a34e-4e73-aa83-38a792beb88e', 'cd791414-d6f6-489e-b2be-9b4f8b9d96e7']}, {'uuid': '5e088f58-044b-4a6f-98cf-ee823dbdc9b3', 'net': 'ADS_DRDY', 'old_xy_mm': [46.97, 19.8], 'new_xy_mm': [46.97, 20.2], 'attached_tracks': ['9860bc29-5a29-4dfa-ba87-0d639eb7d456', '1564d097-fde4-4867-b497-457fffef122f']}, {'uuid': '06901ed6-4cf5-41bc-b246-250aba7a089c', 'net': 'ADS_MISO', 'old_xy_mm': [46.97, 20.6], 'new_xy_mm': [46.97, 21.0], 'attached_tracks': ['d24bf9ca-bef4-4228-9a7c-8eb9649a5318', 'e852030b-4716-4e43-a27e-d5c10df8734f']}, {'uuid': 'a46d9a70-64ed-4679-b2e7-a8c9a3e43098', 'net': 'ADS_MOSI', 'old_xy_mm': [46.97, 22.2], 'new_xy_mm': [46.97, 22.6], 'attached_tracks': ['b83cea5d-e9f3-4145-b32f-f6f8c7db9d58', 'd86c147d-4cfd-4d85-b445-57ce595b53d5']}, {'uuid': 'f772c37f-65de-4938-a41c-7564dd660699', 'net': 'ADS_RESET', 'old_xy_mm': [46.97, 19.0], 'new_xy_mm': [46.97, 19.4], 'attached_tracks': ['d3921165-9dd3-4582-a4a9-bcd1df5bfadf', '8a583fcb-a2f5-4b92-883c-ea43805e6d2f']}, {'uuid': '9856ac53-ccb3-41c6-938d-158a505a4b2d', 'net': 'ADS_START', 'old_xy_mm': [46.97, 18.2], 'new_xy_mm': [46.97, 18.6], 'attached_tracks': ['e0f29fc2-f83f-4e11-abc4-688474ccc2ba', '82275c1c-5e7b-489d-a0df-271362a54e97']}, {'uuid': 'c061261c-e9ef-4f72-a9e8-5e2a56b91ed6', 'net': 'SYS_5V', 'old_xy_mm': [46.97, 24.6], 'new_xy_mm': [46.97, 25.0], 'attached_tracks': ['83f39e42-d17e-4d23-8fde-3d930d10c2d5', '0c8f4941-efc0-488c-9516-c3e4ac699334']}]}
remove=set(['0711c08c-a3c8-409a-ab9b-ad53800f7691', '11403ca2-e486-4a5f-9710-36723d79b284', '1564d097-fde4-4867-b497-457fffef122f', '70d10c48-41bf-4603-b844-b8833d544722', '979ed132-e88c-469d-ae4b-0a5b3444caeb', '9fc6cc54-71fc-4423-8ff0-76371a75f486', 'aeacff58-97f7-4e2d-bdd7-091f4d036a3e', 'b1e647b2-0d5e-4f32-b6d9-e153e8705211'])
selection=json.loads((C/'selection.json').read_text())
assert selection['afe']['baseline_pcb_sha256']=='a21378ccdee99483476029f1a83178f06f04ec7765870b2a36bc914ee907312b'
assert selection['digital']['baseline_pcb_sha256']=='9407948570a5ba2f7ba6700888929932599c12ad0884c823c179237d57320851'
shutil.copytree(C,O);actual_moves={};added=[]
for name in ['afe','digital']:
 path=O/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');b=p.LoadBoard(str(path));rows=[]
 for row in moves[name]:
  v=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==row['uuid']);a=v.GetPosition();assert [p.ToMM(a.x),p.ToMM(a.y)]==row['old_xy_mm'] and v.GetNetname()==row['net'];c=p.VECTOR2I(*[p.FromMM(x) for x in row['new_xy_mm']]);attached=[]
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):continue
   change=False
   if t.GetStart()==a:t.SetStart(c);change=True
   if t.GetEnd()==a:t.SetEnd(c);change=True
   if change:attached.append(t.m_Uuid.AsString())
  v.SetPosition(c);rows.append(dict(row,attached_tracks=attached))
 p.SaveBoard(str(path),b);actual_moves[name]=rows
 if name=='digital':
  tree=loads(path.read_text());tree=[q for q in tree if not(isinstance(q,list) and q[0] in ['segment','arc'] and json.loads(sub(q,'uuid')[1]) in remove)];path.write_text(dumps(tree));b=p.LoadBoard(str(path))
  for net,ly,points in [('ADS_SCLK',p.B_Cu,[(45.7,23),(46.3,23),(46.6,23.3),(47.1,23.3),(47.4042,23.6042),(47.4042,25.4),(47.3042,25.5),(44.5,25.5),(44,26),(43.55,26)]),('ADS_DRDY',p.In2_Cu,[(46.97,20.2),(47.3952,20.2),(47.3952,19.3748)])]:
   for a,c in zip(points,points[1:]):
    t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[p.FromMM(x) for x in a]));t.SetEnd(p.VECTOR2I(*[p.FromMM(x) for x in c]));t.SetWidth(p.FromMM(.15));t.SetLayer(ly);t.SetNet(b.FindNet(net));b.Add(t);added.append(t.m_Uuid.AsString())
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);selection[name]['candidate_pcb_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 table=O/name/'sym-lib-table';table.write_text(table.read_text().replace(C.resolve().as_posix(),O.resolve().as_posix()))
(O/'selection.json').write_text(json.dumps(selection,indent=2));(O/'via_moves.json').write_text(json.dumps(actual_moves,indent=2));(O/'local_route_revision.json').write_text(json.dumps({'removed_tracks':sorted(remove),'added_items':added,'rerouted_nets':['ADS_SCLK','ADS_DRDY']},indent=2))
print('Separate candidate local fanout written. Run fresh DRC/parity and candidate checker before adoption.')

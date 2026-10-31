"""Add explicit assembly-limit tail reservations to the original envelope model."""
from pathlib import Path
import json,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');path=H/'models/JST_S4B_PH_TH_envelope.wrl';s=path.read_text(encoding='utf8');assert '# Trimmed-tail reservation' not in s;boxes=[]
for x in [0,2,4,6]:
 lo=[x-.85,-1.1,-2.8];hi=[x+.85,1.1,-1.6];boxes.append(dict(min=lo,max=hi));pts=[(a/2.54,-b/2.54,c/2.54) for c in [lo[2],hi[2]] for b in [lo[1],hi[1]] for a in [lo[0],hi[0]]];faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];s+='\n# Trimmed-tail reservation: 1.2mm below 1.6mm PCB, not an untrimmed supplier lead.\nShape { appearance Appearance { material Material { diffuseColor .9 .5 .15 transparency .35 } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,v)) for v in pts)+' ] } coordIndex [ '+', '.join(' '.join(map(str,f))+', -1' for f in faces)+' ] } }\n'
path.write_text(s,encoding='utf8');q=H/'review/component_envelopes.json';d=json.loads(q.read_text())
for m in d['models']:
 if m['model']==path.name:m['additional_tail_reservation_boxes_footprint_mm']=boxes;m['scope']='Nominal TH header body plus orange solder/tail reservation below a 1.6mm PCB, assuming trim to <=1.2mm below B. Not supplier CAD or untrimmed lead geometry. Mated plug/wires are separate.';m['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
q.write_text(json.dumps(d,indent=2),encoding='utf8');print('Modeled JH2 trimmed-tail reservations; PCB copper unchanged')

"""Check published passive-FPC prototype bindings; no manufacturing release."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'hardware/YuEEG_8CH_RevH_Stack';D=H/'display_link'
def verify():
 q=json.loads((D/'review/checkpoint.json').read_text());assert q['status']=='PROTOTYPE_NOT_FOR_ORDER'
 sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
 for name,digest in q['source_files_sha256'].items():assert sha(D/name)==digest,'Stale FPC source/report: '+name
 for name,digest in q['baseline_pcb_sha256'].items():assert sha(H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb'))==digest,'Changed FPC baseline: '+name
 drc=json.loads((D/'review/drc_current.json').read_text());erc=json.loads((D/'review/erc_current.json').read_text());fold=json.loads((D/'review/fold_alignment.json').read_text())
 assert all(not drc[k] for k in ['violations','unconnected_items','schematic_parity']) and not any(s['violations'] for s in erc['sheets'])
 assert fold['pcb_sha256']==sha(D/'YuEEG_H_DISPLAY_LINK.kicad_pcb') and not fold['bend_vias'] and not fold['nonparallel_tracks_in_bend']
 assert all(v['error_mm']<1e-5 for v in fold['upper_socket_folded_pad_checks'])
 print('PASS: display FPC prototype source/report bindings, zero static reports and fold geometry. Physical mating and fabrication remain unqualified.')
if __name__=='__main__':verify()

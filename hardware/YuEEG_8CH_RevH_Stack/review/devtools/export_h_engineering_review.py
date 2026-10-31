from pathlib import Path
import json,hashlib,subprocess,shutil,datetime
R=Path('hardware/YuEEG_8CH_RevH_Stack');out=R/'fabrication_engineering';out.mkdir(exist_ok=True);cli='X:/SoftWare/Kicad/bin/kicad-cli.exe';checks=json.loads((R/'review/current_check_summary.json').read_text());records=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for board,cu in [('afe','F.Cu,In1.Cu,In2.Cu,B.Cu'),('digital','F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu'),('power','F.Cu,B.Cu')]:
 base=R/board;stem='YuEEG_H_'+board.upper();pcb=base/(stem+'.kicad_pcb');report=checks['boards'][board];assert sha(pcb)==report['pcb_sha256'];assert all(report[k]==0 for k in ['drc','unconnected','parity','erc'])
 folder=out/board;folder.mkdir(exist_ok=True)
 jobs=[['pcb','export','gerbers',str(pcb),'-o',str(folder)+'/', '--layers',cu+',F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts'],['pcb','export','drill',str(pcb),'-o',str(folder)+'/', '--drill-origin','plot','--excellon-separate-th'],['pcb','export','pos',str(pcb),'-o',str(folder/'placement_front.csv'),'--format','csv','--units','mm','--side','front','--smd-only','--use-drill-file-origin'],['pcb','export','pos',str(pcb),'-o',str(folder/'placement_back.csv'),'--format','csv','--units','mm','--side','back','--smd-only','--use-drill-file-origin']]
 with (folder/'export.log').open('w') as log:
  for args in jobs:subprocess.run([cli,*args],stdout=log,stderr=log,check=True)
 shutil.copy2(base/'BOM.csv',folder/'BOM.csv')
 edge=next(folder.glob('*Edge_Cuts*'));s=edge.read_text()
 if board!='power':
  assert 'X29500000Y-59200000D02*\nX18500000Y-59200000D01*' in s,'Missing 11mm roof of USB mouth relief'
  assert 'X30000000Y-59700000I0J-500000D01*' in s and 'X18500000Y-59200000I500000J0D01*' in s,'Missing R0.5 mouth relief arcs'
  # Native Gerber object attributes bind each pair of semicircles to its hole.
  for ref in ['H1','H2','H3']:
   section=s.split('%TO.C,'+ref+'*%')[1].split('%TO.C,')[0].split('%TD*%')[0]
   assert section.count('I-1200000J0D01')==1 and section.count('I1200000J0D01')==1,(board,ref,'Missing 2.4mm internal opening')
 files={p.name:sha(p) for p in folder.iterdir() if p.is_file() and p.name!='export.log'}
 assert any(n.endswith('.drl') for n in files)
 records.append({'board':board,'pcb_sha256':sha(pcb),'files':files,'internal_M2_openings_in_Edge_Cuts':3 if board!='power' else 0})
(out/'MANIFEST.json').write_text(json.dumps({'status':'ENGINEERING_REVIEW_ONLY_NOT_FOR_ORDER','timestamp':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'boards':records},indent=2))
(out/'README.md').write_text('''# Rev H engineering Gerber / drill / SMT export

**NOT FOR ORDER — mechanical and sourcing gates remain open.** These files are for engineering review, not a released production package. No order ZIP is generated.

AFE: 48×60mm, four copper layers. Digital: 48×60mm, six copper layers. Power strip: 34×18mm, two copper layers. Main board thickness is presently 1.6mm; the power board probe version and thickness are not yet finalized.

AFE and digital each have three 2.4mm round internal openings at (44,4), (44,51), (4,55), represented in **Edge.Cuts**. They are not duplicated as Excellon drill hits. CAM must preserve all three internal circles. M2 mounting screws, spacers and washers must be insulating.

The current power-board JP1 is still a temporary logical terminal; the verified probe reference has not been integrated. Screen FPC reach, support height, battery contact alignment/polarity and exact mating connector procurement remain unresolved. Read `docs/REVH_MECHANICAL_REVIEW.md` and `docs/REVH_NPBX1_POWER.md` before using these exports.

Digital JH2 is now the right-facing TH S4B-PH-K-S. Trim/inspect its solder and tails to <=1.2mm below B; follow docs/REVH_POWER_HARNESS.md.

Front/back SMT positions are exported separately; hand-assembled through-hole connectors, probes and mounting hardware are not an SMT-only placement file. BOM lists and manufacturing stackup/impedance, thermal-via and assembly-process requirements must be reviewed before an actual fabrication release. Clean static checks do not prove assembly, functional acquisition or patient isolation.

`MANIFEST.json` binds each export to its current PCB hash. Regenerate this directory after any board change.
''',encoding='utf8')
print('Engineering exports complete for all three boards; six M2 internal Gerber openings verified')

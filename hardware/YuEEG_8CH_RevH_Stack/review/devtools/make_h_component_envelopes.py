"""Original dimensional envelopes, deliberately not presented as supplier STEP."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');M=R/'models';records=[]
def make(name,boxes,source,note):
 out=['#VRML V2.0 utf8','# Original dimensional envelope; NOT manufacturer CAD. XY follows footprint, Z from mounting plane.']
 for lo,hi,color in boxes:
  # Footprint Y is down; 3D Y is up. VRML library units are 0.1 inch.
  pts=[(x/2.54,-y/2.54,z/2.54) for x,y,z in [(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])]]
  # Mirroring footprint Y changes handedness: reverse every face winding too.
  out.append('Shape { appearance Appearance { material Material { diffuseColor '+color+' } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,p)) for p in pts)+' ] } coordIndex [ 0,1,2,3,-1, 7,6,5,4,-1, 4,5,1,0,-1, 5,6,2,1,-1, 6,7,3,2,-1, 7,4,0,3,-1 ] } }')
 path=M/(name+'.wrl');path.write_text('\n'.join(out)+'\n')
 records.append({'model':path.name,'boxes_footprint_mm':[{'min':lo,'max':hi} for lo,hi,_ in boxes],'source':source,'scope':note,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 return path.name
sw=make('SKRTLBE010_envelope',[((-2.25,-1.35,0),(2.25,1.21,3.3),'.55 .57 .59'),((-1,1.21,.7),(1,2.05,2.7),'.07 .07 .07')],['https://tech.alpsalpine.com/cms.media/product_detail_fig_skrt_d_21_en_3c9d642f3b.gif'],'Nominal body and actuator reach. Rectangular actuator is a bounding approximation, not actual circular geometry; no guide bosses.')
ph=make('JST_S4B_PH_SM4_envelope',[((-5.95,-1.6,0),(5.95,4.4,5.5),'.86 .84 .73')],['https://www.jst-mfg.com/product/pdf/eng/ePH.pdf'],'Nominal SMT side-entry header body only; plug and wire bending volume are separate requirements.')
sd=make('KINGCONN_7TFCN_FA_1010_C_envelope',[((-5.705,-5.2,0),(5.705,.3,3.75),'.56 .58 .60'),((-5.5,.3,2.56),(5.5,9.8,3.56),'.08 .08 .08')],['https://www.kingconn.com.tw/files/7TFCN-FA-1010-X.pdf'],'Nominal short socket body and exposed inserted card. Card underside 2.56 mm; edge shape simplified; socket dimensional tolerances and card insertion sweep not resolved by this envelope.')
ocn=make('OCN_OK_14F024_04_envelope',[((-3.65,-1.25,0),(3.65,1.25,.87),'.28 .27 .23')],['hardware/display-amoled-1.78inch-368x448-main/versions/AM178Q368448LK/cad/OK-14F024-04.pdf'],'Female Rev B page 3; body 7.30 x 2.50, maximum socket height .77+.10. Mated height .80 is not an extension cable allowance.')
ind=make('TDK_SPM4015_LR_envelope',[((-2.3,-2.15,0),(2.3,2.15,1.5),'.19 .20 .21')],['https://product.tdk.com/en/search/inductor/inductor/smd/info?part_no=SPM4015T-1R0M-LR'],'Maximum X/Y based on 4.40/4.10 +/- .20 mm, maximum height 1.50 mm. Leads and magnetic details omitted.')
sot=make('Diodes_SOT523_envelope',[((-.425,-.85,.1),(.425,.85,.9),'.09 .09 .09'),((-.875,-.65,0),(-.425,.65,.2),'.65 .65 .65'),((.425,-.15,0),(.875,.15,.2),'.65 .65 .65')],['https://www.diodes.com/assets/Package-Files/SOT523.pdf'],'Conservative package envelope: D<=1.70, E<=1.75, E1<=.85; A1<=.10 plus A2<=.80 gives .90 mm total upper bound. Lead groups simplified; does not change electrical pin numbering.')
hvboxes=[((-1.55,-1.55,.15),(1.55,1.55,1.1),'.08 .08 .08')]
for yy in [-.975,-.325,.325,.975]:
 for xx in [-1,1]:
  hvboxes.append((((-2.525 if xx<0 else 1.55),yy-.19,0),((-1.55 if xx<0 else 2.525),yy+.19,.38),'.65 .65 .65'))
hv=make('TI_DGN8_envelope',hvboxes,['https://www.ti.com/lit/gpn/TPS7A49'],'DGN outline: body <=3.1 x 3.1, lead span <=5.05, height <=1.1 mm. Simplified leads; no assertion about internal die, paste coverage or the exact ordered DGN thermal-pad variant.')
mapping={'YuEEG:ALPS_SKRTLBE010_GroundedShell':sw,'Connector_JST:JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal':ph,'YuEEG:KINGCONN_7TFCN_FA_1010_C_NotchedShield':sd,'YuEEG:OCN_OK_14F024_04':ocn,'YuEEG:TDK_SPM4015_LR':ind}
mapping.update({'Package_TO_SOT_SMD:SOT-523':sot,'Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm':hv,'Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm':'${KICAD9_3DMODEL_DIR}/Package_SON.3dshapes/WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm.step'})
def bind(d,name):
 d[:]=[n for n in d if not(isinstance(n,list) and n[0]=='model')]
 d.append(['model',json.dumps(name if name.startswith('${') else '${KIPRJMOD}/../models/'+name),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]])
for key,name in mapping.items():
 lib,fp=key.split(':');path=R/'footprints'/(lib+'.pretty')/(fp+'.kicad_mod');d=loads(path.read_text());bind(d,name);path.write_text(dumps(d))
installed=[]
for board in ['afe','digital','power']:
 path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');d=loads(path.read_text())
 for f in d:
  if not(isinstance(f,list) and f[0]=='footprint'):continue
  key=json.loads(f[1])
  if key in mapping:
   bind(f,mapping[key]);ref=next(json.loads(q[2]) for q in f if isinstance(q,list) and q[0]=='property' and q[1]=='"Reference"');installed.append({'board':board,'reference':ref,'model':mapping[key]})
 path.write_text(dumps(d))
(R/'review/component_envelopes.json').write_text(json.dumps({'models':records,'bindings':installed,'standard_model_aliases':{'power.UP1':'Installed KiCad generic WSON-8 2x2, pitch .5, EP .9x1.6 body model replaces missing Texas-named model. Visual package alias only; original Texas footprint retained.'},'status':'Dimensional envelopes only. Not a full tolerance/assembly/cable reach/isolation approval.'},indent=2))
print('Created',len(records),'original envelopes;',len(installed),'native PCB bindings')

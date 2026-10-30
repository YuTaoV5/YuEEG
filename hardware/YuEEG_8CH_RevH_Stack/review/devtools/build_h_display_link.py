"""Short passive FPC extension prototype; baseline three boards are unchanged.

Both connectors mount on B in the flat artwork. A 180-degree U fold turns the
upper socket upward. Pin mapping is geometric/project-logical, not vendor pin-1
certification. Physical mating, fabrication and full 3D fit remain release gates.
"""
from pathlib import Path
import json,math,sys,uuid,csv,copy,subprocess,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'display_link';D.mkdir(exist_ok=True);(D/'review').mkdir(exist_ok=True);F=D/'footprints/YuEEG_Display.pretty';F.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path('hardware/YuEEG_8CH_RevG/review').resolve()));from sexpr_io import loads,dumps,sub
thickness=.11;mated=.8;height=6.;straight=1.85;radius=1.8;vertical=height-2*mated-thickness-2*radius;assert vertical>0;span=2*straight+math.pi*radius+vertical;male_y=1.8;female_y=male_y+span;W=8.3;B=female_y+1.8;stem='YuEEG_H_DISPLAY_LINK'
mp=json.loads((H/'digital/review/expected_connections.json').read_text());pins={str(i):mp['J2002.'+str(i)] for i in range(1,29)}
male='OCN_OK_14GM024_04_LogicalMate';female='OCN_OK_14F024_04_GangMask'
# Manufacturer male land pattern: outer/inner row span 2.40/1.10 -> y=.875,
# length=.65. Retention outer/inner 1.66/.60 -> y=.565,length=.53.
items=['(footprint "'+male+'" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd)', '(descr "OCN male 24-contact Rev A p1; project logical mating columns. Sample continuity/orientation unverified.")','(property "Reference" "REF**" (at 0 -2.2) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12))))','(property "Value" "OK-14GM024-04" (at 0 2.2) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12))))','(fp_rect (start -3.3 -1) (end 3.3 1) (stroke (width .1) (type solid)) (fill none) (layer "F.Fab"))','(fp_rect (start -3.55 -1.45) (end 3.55 1.45) (stroke (width .05) (type solid)) (fill none) (layer "F.CrtYd"))']
for i in range(12):
 x=2.2-.4*i
 for n,y in [(i+1,.875),(24-i,-.875)]:items.append(f'(pad "{n}" smd rect (at {x:.3f} {y}) (size .23 .65) (layers "F.Cu" "F.Paste"))')
for n,x,y in [(25,-3.005,.565),(26,-3.005,-.565),(27,3.005,-.565),(28,3.005,.565)]:items.append(f'(pad "{n}" smd rect (at {x} {y}) (size .45 .53) (layers "F.Cu" "F.Paste"))')
items.append('(fp_rect (start -3.35 -1.3) (end 3.35 1.3) (stroke (width 0) (type solid)) (fill solid) (layer "F.Mask")))');(F/(male+'.kicad_mod')).write_text('\n'.join(items))
fp=loads((H/'footprints/YuEEG.pretty/OCN_OK_14F024_04.kicad_mod').read_text());fp[1]=json.dumps(female)
for q in fp:
 if isinstance(q,list) and q[0]=='pad':ls=sub(q,'layers');ls[:]=[v for v in ls if v!='"F.Mask"']
fp[:]=[q for q in fp if not(isinstance(q,list) and q[0].startswith('fp_') and sub(q,'layer') and sub(q,'layer')[1]=='"F.SilkS"')]
fp.append(['fp_rect',['start','-3.6','-1.55'],['end','3.6','1.55'],['stroke',['width','0'],['type','solid']],['fill','solid'],['layer','"F.Mask"']]);(F/(female+'.kicad_mod')).write_text(dumps(fp))
for name in [male,female]:
 fpath=F/(name+'.kicad_mod');data=loads(fpath.read_text());sub(data,'attr').append('allow_soldermask_bridges');fpath.write_text(dumps(data))
# Passive connector schematic, including all four grounded retention fittings.
src=Path('hardware/YuEEG_8CH_RevA/review/build_schematic.py').read_text(encoding='utf8').split('sheets=[]')[0].replace('2026-10-24','2026-10-31').replace('A0 review','H FPC prototype').replace('BATTERY ONLY - NOT VALIDATED FOR HUMAN CONNECTION','DISPLAY LINK PROTOTYPE - MATING AND FLEX NOT QUALIFIED')
ns={'__file__':str(Path('hardware/YuEEG_8CH_RevA/review/build_schematic.py').resolve())};exec(src,ns);ns['load']('Connector_Generic','Conn_01x28');ns.update(ROOT=D,PROJECT=stem,rootid=str(uuid.uuid4()),bom=[],expected={},components={},globals_={v for v in pins.values() if v is not None});sh=ns['Sheet']('display_link','Passive extension / same logical pin at both ends',2);sh.text('DISPLAY FPC EXTENSION / PROTOTYPE / NOT FOR ORDER',20,12,2)
for ref,name,x in [('JF1',male,101.6),('JF2',female,294.64)]:sh.named('Connector_Generic:Conn_01x28',ref,'OK-14GM024-04 / MAIN' if ref=='JF1' else 'OK-14F024-04 / SCREEN',x,121.92,pins,footprint='YuEEG_Display:'+name)
sh.write();root=ns['rootid'];eff=ns['eff'];(D/(stem+'.kicad_sch')).write_text(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root}") (paper "A3") (lib_symbols) (sheet_instances (path "/" (page "1"))) (sheet (at 20 30) (size 150 35) (stroke (width .15) (type default)) (fill (color 0 0 0 0)) (uuid "{sh.id}") (property "Sheetname" "display_link" (at 20 29 0) {eff()}) (property "Sheetfile" "display_link.kicad_sch" (at 20 66 0) {eff()}) (instances (project "{stem}" (path "/{root}" (page "2"))))) (embedded_fonts no))')
(D/'review/expected_connections.json').write_text(json.dumps(ns['expected'],indent=2))
with (D/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=ns['bom'][0]);w.writeheader();w.writerows(ns['bom'])
lib=copy.deepcopy(ns['library']['Connector_Generic:Conn_01x28']);lib[1]='Conn_01x28';(D/'Connector_Generic.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")'+ns['atom'](lib)+')')
(D/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Connector_Generic") (type "KiCad") (uri "${KIPRJMOD}/Connector_Generic.kicad_sym") (options "") (descr "Pinned passive connector")))');(D/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "YuEEG_Display") (type "KiCad") (uri "${KIPRJMOD}/footprints/YuEEG_Display.pretty") (options "") (descr "OCN drawing-derived prototype")))')
pro=json.loads((H/'power/YuEEG_H_POWER.kicad_pro').read_text());settings=pro['board']['design_settings'];settings['drc_exclusions']=[];settings['rules']['min_clearance']=.1;settings['rules']['min_track_width']=.1;settings['rules']['min_via_diameter']=.3;settings['rules']['min_through_hole_diameter']=.1
settings['rules']['min_copper_edge_clearance']=.25;settings['rules']['min_silk_clearance']=.1
pro['net_settings']['classes']=[pro['net_settings']['classes'][0]];pro['net_settings']['classes'][0].update(clearance=.1,track_width=.1,via_diameter=.3,via_drill=.1);pro['net_settings']['netclass_patterns']=[];(D/(stem+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
cad=Path('hardware/display-amoled-1.78inch-368x448-main/versions/AM178Q368448LK/cad/OK-14F024-04.pdf')
(D/'review/design_contract.json').write_text(json.dumps({'status':'FPC_EXTENSION_PROTOTYPE_NOT_FOR_ORDER','outline_mm':[W,B],'neck_width_mm':6.6,'finished_fpc_thickness_mm':thickness,'copper_layers':2,'connector_centers_flat_mm':{'JF1':[W/2,male_y],'JF2':[W/2,female_y]},'B_side_rotations_deg':{'JF1':0,'JF2':0},'connector_mounting_plane_separation_target_mm':height,'warning_plane_datum':'6 mm is between main PCB and factory male FPC solder mounting plane, not a verified screen-back spacing. Factory folded FPC offset remains unknown.','U_fold_neutral_radius_mm':radius,'vertical_centerline_section_mm':vertical,'straight_center_to_bend_mm':straight,'bend_interval_flat_y_mm':[male_y+straight,female_y-straight],'pins':pins,'drawing_path':cad.as_posix(),'drawing_sha256':hashlib.sha256(cad.read_bytes()).hexdigest(),'male_drawing_page':1,'female_drawing_page':3,'fabrication_reference':'https://jlcpcb.com/capabilities/flex-pcb-capabilities','fabrication_proposal':'Two-layer PI FPC, nominal .11 mm finished, 12um copper; end PI stiffeners on F side, .20mm proposal. Advanced .10/.30mm drill/diameter vias in end areas only require fabricator confirmation. Yellow coverlay, gang opening under each fine-pitch connector. Final fab stackup, thickness maximum for bend radius, stiffener support and assembly process not qualified.','procurement':'User confirmed both exact-series male and matching socket are available on Taobao. Specific SKU, delivered version and mating samples have not been independently verified.','scope':'Baseline three boards unchanged. Four unused signal pins remain NC at both ends. Retention fittings remain acquisition GND. Both components on B in flat artwork; one-time U fold toward +Y with a narrow neck to avoid adjacent power ICs. Geometric mating/numbering and all clearances require sample verification.'},indent=2))
for args,out in [(['erc','--format','json'],'erc_current.json'),(['export','netlist','--format','kicadxml'],'netlist.xml')]:subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','sch',*args,'-o',str(D/'review'/out),str(D/(stem+'.kicad_sch'))],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
print('Display link schematic; flat size',round(W,3),'x',B,'radius',radius,'ERC',sum(len(s['violations']) for s in json.loads((D/'review/erc_current.json').read_text(encoding='utf8'))['sheets']))





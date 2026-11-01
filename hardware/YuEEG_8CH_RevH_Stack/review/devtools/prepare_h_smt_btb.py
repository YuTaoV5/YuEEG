"""Make a separate routed-board candidate; never replace the current source PCB.

JMEconn drawing B, public 2017-02-17 drawing, two pages. Project logical
numbering is deliberate: the supplier drawing does not assign contact numbers.
The male footprint is mirrored so the *assembled* pad/net pairs coincide.
"""
from pathlib import Path
import sys, json, shutil, hashlib, csv, copy, uuid
import pcbnew as p, wx
wx.DisableAsserts()
sys.path.insert(0, 'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads, dumps, sub
H = Path('hardware/YuEEG_8CH_RevH_Stack')
C = Path('logs/revh_smt_btb_candidate')
assert not C.exists(), 'Candidate already exists: inspect it rather than resetting work'
Q = json.dumps
for _name in ['afe','digital']:
    _board=p.LoadBoard(str(H/_name/('YuEEG_H_'+_name.upper()+'.kicad_pcb')))
    _part=next(f for f in _board.GetFootprints() if f.GetReference()=='JH1')
    assert _part.GetAttributes() & p.FP_THROUGH_HOLE, 'One-time migration requires the pre-SMT b67843f source; no current files changed'
source = 'https://www.wzjm5001.com/data/upload/2022-03-18/62342c4418c0d.pdf'
def prop(n, key):
    return next(z for z in n if isinstance(z, list) and z[:2] == ['property', Q(key)])
def envelope(name, height, male):
    # Native KiCad VRML coordinates use 0.1 inch. Own bounding model only.
    boxes = [([-4.95,-2.2,0],[4.95,2.2,height],'.08 .08 .08')]
    if male:
        for yy in [-.95,.95]:
            boxes.append(([-4.1,yy-.15,height],[4.1,yy+.15,height+1.9],'.65 .55 .25'))
    for xx in [-4.5,4.5]:
        boxes.append(([xx-.25,1,-.6],[xx+.25,1.5,0],'.08 .08 .08'))
    text=['#VRML V2.0 utf8', '# Original nominal bounding illustration, NOT manufacturer CAD.']
    for lo,hi,col in boxes:
        cen=[(lo[i]+hi[i])/2/2.54 for i in range(3)];size=[(hi[i]-lo[i])/2.54 for i in range(3)]
        text.append('Transform { translation '+' '.join(map(str,cen))+' children [ Shape { appearance Appearance { material Material { diffuseColor '+col+' } } geometry Box { size '+' '.join(map(str,size))+' } } ] }')
    (H/'models'/name).write_text('\n'.join(text)+'\n',encoding='utf8')
for male in [False, True]:
    name='JME_BTB0840_20MR_Logical' if male else 'JME_BTB0845_20FR_Logical'
    model=name+'.wrl';envelope(model,4.0 if male else 4.5,male)
    s=f'''(footprint "{name}" (version 20241229) (generator "YuEEG") (layer "F.Cu")
      (descr "JMEconn 0.8mm dual slot SMT BTB 20 contacts; 8.5mm mated pair; project logical numbering, see REVH_SMT_BTB.md")
      (tags "SMT mezzanine BTB 0.8mm 20 contacts 8.5mm")
      (property "Reference" "REF**" (at 0 -4.1) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12))))
      (property "Value" "{name}" (at 0 4.1) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12))))
      (attr smd)
      (fp_rect (start -4.95 -2.2) (end 4.95 2.2) (stroke (width .1) (type default)) (fill none) (layer "F.Fab"))
      (fp_rect (start -5.2 -3.15) (end 5.2 3.15) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))
      (fp_line (start -4.95 -2.75) (end -4.95 2.75) (stroke (width .12) (type default)) (layer "F.SilkS"))
      (fp_line (start 4.95 -2.75) (end 4.95 2.75) (stroke (width .12) (type default)) (layer "F.SilkS"))
    '''
    for i in range(10):
        for odd,yy in [(True,2),(False,-2)]:
            num=2*i+(1 if odd else 2);yy=-yy if male else yy
            s+=f'(pad "{num}" smd rect (at {-3.6+.8*i:.3f} {yy}) (size .35 1.8) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    for xx in [-4.5,4.5]:
        s+=f'(pad "" np_thru_hole circle (at {xx} 1.25) (size .65 .65) (drill .65) (layers "*.Cu" "*.Mask"))\n'
    # Recommended surface NO CIRCUIT AREA between rows. Buried routing is allowed.
    s+=f'''(zone (net 0) (net_name "") (layer "F.Cu") (uuid "{uuid.uuid4()}") (name "JME_BTB_SURFACE_NO_CIRCUIT")
      (hatch edge .5) (connect_pads (clearance 0)) (min_thickness .15) (filled_areas_thickness no)
      (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed))
      (placement (enabled no) (sheetname "")) (fill (thermal_gap .3) (thermal_bridge_width .3))
      (polygon (pts (xy -4 -1.1) (xy 4 -1.1) (xy 4 1.1) (xy -4 1.1))))
      (model "${{KIPRJMOD}}/../models/{model}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))'''
    (H/'footprints/YuEEG.pretty'/(name+'.kicad_mod')).write_text(s,encoding='utf8')
C.mkdir(parents=True)
for folder in ['afe','digital','footprints','models','libraries']:
    shutil.copytree(H/folder,C/folder)
shutil.copy2(H/'YuEEG.kicad_sym',C/'YuEEG.kicad_sym')
records={}
for board,male in [('afe',False),('digital',True)]:
    base=C/board;path=base/('YuEEG_H_'+board.upper()+'.kicad_pcb');b=p.LoadBoard(str(path))
    old=next(f for f in b.GetFootprints() if f.GetReference()=='JH1')
    assert old.GetAttributes() & p.FP_THROUGH_HOLE, 'Only convert the old THT baseline'
    mapping={q.GetNumber():q.GetNetname() for q in old.Pads()}
    name='JME_BTB0840_20MR_Logical' if male else 'JME_BTB0845_20FR_Logical'
    value='5001-BTB0840-20MR / SMT BTB' if male else '5001-BTB0845-20FR / SMT BTB'
    tmp=p.BOARD();tmp.SetCopperLayerCount(6 if male else 4)
    f=p.FootprintLoad(str(C/'footprints/YuEEG.pretty'),name);tmp.Add(f)
    f.SetReference('JH1');f.SetValue(value);f.SetFPID(p.LIB_ID('YuEEG',name))
    f.SetPosition(p.VECTOR2I(p.FromMM(43.7),p.FromMM(21)))
    if male:f.Flip(f.GetPosition(),False)
    f.SetOrientationDegrees(90)
    f.Reference().SetLayer(p.B_Fab if male else p.F_Fab);f.Value().SetLayer(p.B_Fab if male else p.F_Fab)
    for pad in f.Pads():
        if not pad.GetNumber():continue
        n=p.NETINFO_ITEM(tmp,mapping[pad.GetNumber()]);tmp.Add(n);pad.SetNet(n)
    tf=C/('temp_'+board+'.kicad_pcb');p.SaveBoard(str(tf),tmp)
    new=next(z for z in loads(tf.read_text(encoding='utf8')) if isinstance(z,list) and z[0]=='footprint')
    tree=loads(path.read_text(encoding='utf8'));raw=next(z for z in tree if isinstance(z,list) and z[0]=='footprint' and prop(z,'Reference')[2]=='"JH1"')
    nets={json.loads(sub(q,'net')[2]):sub(q,'net')[1] for q in raw if isinstance(q,list) and q[0]=='pad' and sub(q,'net')}
    for q in new:
        if isinstance(q,list) and q[0]=='pad' and sub(q,'net'):sub(q,'net')[1]=nets[json.loads(sub(q,'net')[2])]
    new.append(copy.deepcopy(sub(raw,'path')));tree[tree.index(raw)]=new;path.write_text(dumps(tree),encoding='utf8')
    for sp in base.glob('circuit_*.kicad_sch'):
        d=loads(sp.read_text(encoding='utf8'));changed=False
        for sym in d:
            if isinstance(sym,list) and sym[0]=='symbol' and prop(sym,'Reference')[2]=='"JH1"':
                prop(sym,'Value')[2]=Q(value);prop(sym,'Footprint')[2]=Q('YuEEG:'+name);prop(sym,'Datasheet')[2]=Q(source);changed=True
        if changed:sp.write_text(dumps(d),encoding='utf8')
    rows=list(csv.DictReader((base/'BOM.csv').open(encoding='utf-8-sig')))
    for row in rows:
        if row['Reference']=='JH1':row.update(Value=value,Footprint='YuEEG:'+name,Datasheet=source)
    with (base/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as out:
        w=csv.DictWriter(out,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    records[board]={'baseline_sha256':hashlib.sha256((H/board/path.name).read_bytes()).hexdigest(),'logical_pins':mapping,'candidate_center_mm':[43.7,21],'orientation_deg':90,'footprint':'YuEEG:'+name}
    print(board,'candidate prepared; old copper retained for local rerouting',flush=True)
(C/'baseline.json').write_text(json.dumps(records,indent=2),encoding='utf8')

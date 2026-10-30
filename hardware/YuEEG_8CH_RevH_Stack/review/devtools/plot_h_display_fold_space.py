"""Conditional local 3D envelope view, not an enclosure or assembly release."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from check_h_display_fold_space import sweep,q,center
D=Path('hardware/YuEEG_8CH_RevH_Stack/display_link');r=json.loads((D/'review/fold_space.json').read_text());fig=plt.figure(figsize=(12,7));ax=fig.add_subplot(121,projection='3d');cx,cy=center
def box(bb,col,alpha):
 x,y,z,X,Y,Z=bb;v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)];ids=[[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]];ax.add_collection3d(Poly3DCollection([[v[i] for i in ids_] for ids_ in ids],facecolor=col,edgecolor=col,alpha=alpha,linewidth=.3))
cells=sweep(q)
for c in cells[::18]:box(c,'#b58c22',.55)
names=['U1001','U1003','U402_max_package_plus_solder','R1101_conditional_low_profile']
for n in names:
 row=next(v for v in r['neighbors'] if v['ref']==n)
 for bb in row.get('boxes',[row['box']]):box(bb,'#476f99',.3)
 b=row['box'];ax.text((b[0]+b[3])/2,(b[1]+b[4])/2,b[5]+.3,n.split('_')[0],fontsize=8)
ax.set(xlim=(24,37),ylim=(20,30),zlim=(0,6.5),xlabel='Main X / mm',ylabel='Main Y / mm',zlabel='Z / mm',title='Local nominal envelopes');ax.set_box_aspect((13,10,6.5));ax.view_init(elev=28,azim=-55)
tx=fig.add_subplot(122);tx.axis('off');lines=['Fold-space review — conditional','', 'FPC: 8.0 x 13.531 mm flat / neck 5.1 mm','Neutral bend radius: 1.7 mm','Main PCB to factory FPC solder plane: 6 mm','', 'Nominal distances to conservative boxes:']
for n in names:
 row=next(v for v in r['neighbors'] if v['ref']==n);lines.append(n.split('_')[0]+': '+f"{row['minimum_nominal_box_distance_mm']:.3f}"+' mm')
lines.extend(['','U1001 / U1003: flash + .10 mm solder lift','U402: max package plus 0.10 mm solder lift','R1101: conditional low-profile part + solder','', 'Not all assembly tolerances are included.','Factory screen FPC/back still unmeasured.','Gold: flex / end stiffeners / connectors','Blue: selected component envelope boxes','', 'PROTOTYPE — NOT FOR ORDER'])
for i,line in enumerate(lines):tx.text(0,1-i*.043,line,fontsize=11 if i else 13,va='top',weight='bold' if i in [0,len(lines)-1] else 'normal')
ax.set_position([.00,.08,.48,.84]);tx.set_position([.57,.05,.42,.90]);fig.savefig(D/'review/fold_space.png',dpi=180);fig.savefig(D/'review/fold_space.svg');print('Local fold-space views saved')

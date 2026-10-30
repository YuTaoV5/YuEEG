"""Illustrative native copper and nominal fold; not an assembly drawing."""
from pathlib import Path
import json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
D=Path('hardware/YuEEG_8CH_RevH_Stack/display_link');q=json.loads((D/'review/design_contract.json').read_text());g=json.loads((D/'review/geometry.json').read_text());W,H=q['outline_mm'];a,c=q['bend_interval_flat_y_mm']
fig,axs=plt.subplots(1,3,figsize=(13,7));fig.suptitle('YuEEG display FPC prototype — NOT FOR ORDER',fontsize=16)
for ax,layer,color in [(axs[0],'F.Cu','#d64a31'),(axs[1],'B.Cu','#2369a7')]:
 ax.axhspan(a,c,color='#e6dab9',alpha=.45);ax.text(.2,(a+c)/2,'BEND',rotation=90,fontsize=9)
 for s,e in g['edges']:ax.plot([s[0],e[0]],[s[1],e[1]],color='black',lw=1)
 for t in g['tracks']:
  if 'via' in t:ax.add_patch(plt.Circle(t['via'],t['width']/2,color='#50387c'))
  elif t['layer']==layer:ax.plot([t['start'][0],t['end'][0]],[t['start'][1],t['end'][1]],color=color,lw=max(.5,t['width']*6),solid_capstyle='round')
 for p in g['pads']:
  if layer=='B.Cu':
   x,y=p['xy'];sx,sy=p['size'];ax.add_patch(Rectangle((x-sx/2,y-sy/2),sx,sy,color='#bc902e'))
   if p['pin']=='1':ax.text(x+.18,y,'1',fontsize=8)
 for ref,xy in q['connector_centers_flat_mm'].items():ax.text(.1,xy[1]-1.55,ref,fontsize=9)
 ax.set(xlim=(-.5,W+.5),ylim=(H+.5,-.5),title=layer+' / flat view from F side',xlabel='mm',ylabel='mm');ax.set_aspect('equal');ax.grid(alpha=.15)
axs[0].set_title('F.Cu / flat view from F side\nEnd ground pours omitted',fontsize=11)
ax=axs[2];r=q['U_fold_neutral_radius_mm'];v=q['vertical_centerline_section_mm'];s=q['straight_center_to_bend_mm'];z=.8+.055
xs=[0,s];zs=[z,z]
for i in range(1,51):
 t=(math.pi/2)*i/50;xs.append(s+r*math.sin(t));zs.append(z+r*(1-math.cos(t)))
xs.append(s+r);zs.append(z+r+v)
for i in range(1,51):
 t=(math.pi/2)*i/50;xs.append(s+r*math.cos(t));zs.append(z+r+v+r*math.sin(t))
xs.append(0);zs.append(z+2*r+v)
ax.plot(xs,zs,color='#b17e19',lw=4);ax.plot([-.7,1.3],[0,0],color='black',lw=3);ax.plot([-.7,1.3],[6,6],color='black',lw=3)
ax.add_patch(Rectangle((-.5,.05),1,.7,color='#6f8191'));ax.add_patch(Rectangle((-.5,5.25),1,.7,color='#6f8191'))
ax.text(-.6,-.6,'Main PCB');ax.text(-.6,6.4,'Factory FPC solder plane');ax.text(4.1,3,'6.0 mm target',rotation=90,va='center');ax.annotate('',(3.9,6),(3.9,0),arrowprops=dict(arrowstyle='<->'))
ax.text(-.6,9.7,'Screen-back offset unknown\nConnectors symbolic\nPI stiffeners only on flat ends\nBend neutral radius 1.7 mm\nNo pad/via in bend',fontsize=10,va='top');ax.set(xlim=(-1,6),ylim=(-1,11),title='Nominal U fold toward +Y',xlabel='relative Y / mm',ylabel='Z / mm');ax.set_aspect('equal');ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(D/'review/flat_and_fold.png',dpi=180);fig.savefig(D/'review/flat_and_fold.svg');print('Display FPC review views saved')

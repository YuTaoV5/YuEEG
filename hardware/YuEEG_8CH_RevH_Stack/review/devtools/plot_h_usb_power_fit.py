from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path('hardware/YuEEG_8CH_RevH_Stack/mechanical/current');d=json.loads((R/'usb_power_fit_candidate.json').read_text());W,H=d['outline_mm']
fig,axs=plt.subplots(1,2,figsize=(13,5.8));fig.suptitle('USB + power strip feasibility: 43 x 23.6 mm',fontsize=16,y=.96)
fig.text(.5,.895,'UNROUTED EXPERIMENT / NOT FOR ORDER / battery contacts and new cable are unresolved',ha='center',color='#aa263d',fontsize=10)
for ax,side in zip(axs,['F','B']):
 ax.add_patch(Rectangle((0,0),W,H,facecolor='#f4f6f8',edgecolor='#34495e',linewidth=1.5))
 for ref,r in d['courtyards'].items():
  if r['side']!=side:continue
  x,y,x2,y2=r['bounds_mm'];host=ref in {'J601','R701','R702','C701','C702','C901','D602','D603','D604','D605','D901','F901','R901','R902'}
  ax.add_patch(Rectangle((x,y),x2-x,y2-y,facecolor='#d7c7ef' if host else '#b8dddf',edgecolor='#52616a',linewidth=.6))
  ax.text((x+x2)/2,(y+y2)/2,ref,fontsize=7,ha='center',va='center')
 for x,y,x2,y2 in d['probe_reservations_mm']:
  ax.add_patch(Rectangle((x,y),x2-x,y2-y,facecolor='none',edgecolor='#c0392b',linewidth=1.3,linestyle='--'))
 ax.set_title(('Front' if side=='F' else 'Back')+' - same XY view, back is not mirrored',fontsize=11)
 ax.set_xlim(-1,W+1);ax.set_ylim(H+1,-1);ax.set_aspect('equal');ax.set_xlabel('mm');ax.set_ylabel('mm');ax.grid(alpha=.15)
fig.text(.5,.075,'Blue: acquisition/power or isolator body   Purple: USB host parts   Red: unverified probe/tool reservations',ha='center',fontsize=10)
fig.text(.5,.035,f"37 parts / {len(d['back_smt'])} back SMT / {d['native_unconnected_items']} unrouted items / native DRC still has {sum(d['native_drc_violation_types'].values())} violations",ha='center',fontsize=10,color='#aa263d')
fig.subplots_adjust(top=.82,bottom=.15,wspace=.16);fig.savefig(R/'usb_power_fit_overview.png',dpi=160);fig.savefig(R/'usb_power_fit_overview.svg');print('Fit overview plotted from native courtyard evidence')

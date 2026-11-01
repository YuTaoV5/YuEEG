from pathlib import Path
import re,json,uuid,math,csv
ROOT=Path(__file__).resolve().parents[1]
LIB=Path('X:/SoftWare/Kicad/share/kicad/symbols')
def parse(s):
    ts=re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',s); stack=[]; out=[]
    for t in ts:
        if t=='(': stack.append([])
        elif t==')':
            n=stack.pop()
            if stack: stack[-1].append(n)
            else: out=n
        else: stack[-1].append(json.loads(t) if t.startswith('"') else (float(t) if re.fullmatch(r'-?\d+(\.\d+)?',t) else t))
    return out
def sub(n,k): return next((x for x in n if isinstance(x,list) and x[0]==k),None)
def children(n,k): return [x for x in n if isinstance(x,list) and x[0]==k]
def atom(v):
    if isinstance(v,list): return '('+str(v[0])+' '+ ' '.join(atom(x) for x in v[1:])+')'
    if isinstance(v,(int,float)): return str(round(v,4))
    if v in {'yes','no','default','none','background','outline','input','output','passive','power_in','power_out','bidirectional','open_collector','line','left','right','top','bottom'}: return v
    return json.dumps(str(v),ensure_ascii=False)
def q(s):return json.dumps(str(s),ensure_ascii=False)
def uid():return str(uuid.uuid4())
def eff(size=1.27,extra=''):return f'(effects (font (size {size} {size})) {extra})'
library={}
def load(lib,name):
    key=lib+':'+name
    if key in library:return library[key]
    tree=parse((LIB/(lib+'.kicad_sym')).read_text(encoding='utf-8'))
    n=next(x for x in children(tree,'symbol') if x[1]==name)
    if sub(n,'extends'):raise ValueError('extends '+key)
    # Keep original syntax for library symbols via serializer (all atom names quoted are legal in s-expr).
    library[key]=n
    return n
def pin(num,name,x,y,angle,typ='passive'):
    return ['pin',typ,'line',['at',x,y,angle],['length',2.54],['name',name,['effects',['font',['size',1,1]]]],['number',str(num),['effects',['font',['size',1,1]]]]]
def custom(name,units,footprint,datasheet):
    n=['symbol',name,['pin_names',['offset',0.6]],['in_bom','yes'],['on_board','yes']]
    for k,v in [('Reference','U'),('Value',name),('Footprint',footprint),('Datasheet',datasheet)]: n.append(['property',k,v,['at',0,0,0],['effects',['font',['size',1.27,1.27]]]])
    for u,(w,h,pins) in enumerate(units,1):
        n.append(['symbol',f'{name}_{u}_1',['rectangle',['start',-w,h],['end',w,-h],['stroke',['width',0.254],['type','default']],['fill',['type','background']]],*pins])
    library['YuEEG:'+name]=n
    return n
def boxpins(items,side,w=15.24,start=20.32,step=5.08):
    return [pin(num,name,(-w-2.54 if side=='L' else w+2.54),start-i*step,(0 if side=='L' else 180),typ) for i,(num,name,typ) in enumerate(items)]
ads_units=[]
for base in [0,4]:
    items=[]
    for i in range(base+1,base+5):items += [(18-2*i,f'IN{i}P','input'),(17-2*i,f'IN{i}N','input')]
    ads_units.append((15.24,22.86,boxpins(items,'L',start=17.78)))
ads_units.append((15.24,27.94,boxpins([(34,'DIN','input'),(40,'SCLK','input'),(39,'~{CS}','input'),(36,'~{RESET}','input'),(35,'~{PWDN}','input'),(38,'START','input'),(52,'CLKSEL','input'),(37,'CLK','input'),(41,'DAISY_IN','input'),(31,'RESV1','input')],'L',start=22.86)+boxpins([(43,'DOUT','output'),(47,'~{DRDY}','output'),(42,'GPIO1','bidirectional'),(44,'GPIO2','bidirectional'),(45,'GPIO3','bidirectional'),(46,'GPIO4','bidirectional')],'R',start=22.86)))
ads_units.append((15.24,20.32,boxpins([(17,'SRB1','input'),(18,'SRB2','input'),(60,'BIASREF','input'),(61,'BIASINV','input'),(62,'BIASIN','input')],'L',start=12.7)+boxpins([(63,'BIASOUT','output'),(24,'VREFP','output'),(25,'VREFN','power_in'),(64,'RESERVED','passive')],'R',start=12.7)))
ads_units.append((15.24,38.1,boxpins([(n,'AVDD' if n!=54 else 'AVDD1','power_in') for n in [19,21,22,56,59,54]]+[(48,'DVDD','power_in'),(50,'DVDD','power_in')],'L',start=30.48)+boxpins([(n,'AVSS' if n!=53 else 'AVSS1','power_in') for n in [20,23,32,57,58,53]]+[(n,'DGND','power_in') for n in [33,49,51]]+[(28,'VCAP1','output'),(30,'VCAP2','output'),(55,'VCAP3','output'),(26,'VCAP4','output'),(27,'NC','passive'),(29,'NC','passive')],'R',start=33.02,step=5.08)))
custom('ADS1299PAG',ads_units,'Package_QFP:TQFP-64_10x10mm_P0.5mm','https://www.ti.com/lit/ds/symlink/ads1299.pdf')
custom('TPS7A4901DGN',[(10.16,15.24,boxpins([(8,'IN','power_in'),(5,'EN','input'),(6,'NR/SS','passive')],'L',w=10.16,start=7.62)+boxpins([(1,'OUT','power_out'),(2,'FB','input'),(3,'NC','passive'),(7,'DNC','passive')],'R',w=10.16,start=10.16)+[pin(4,'GND',0,-17.78,90,'power_in'),pin(9,'EP',5.08,-17.78,90,'power_in')])],'Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm','https://www.ti.com/lit/gpn/TPS7A49')
# Nexperia BAV199 series pair: 1=A1, 2=K2, 3=K1/A2.
custom('BAV199',[(5.08,5.08,[pin(1,'A1',-7.62,2.54,0),pin(2,'K2',7.62,2.54,180),pin(3,'K1/A2',0,-7.62,90)])],'Package_TO_SOT_SMD:SOT-23','https://assets.nexperia.com/documents/data-sheet/BAV199.pdf')
for lib,name in [('Device','R'),('Device','C'),('Device','C_Polarized'),('Device','L'),('Device','D_Schottky'),('Device','Fuse'),('Switch','SW_SPST'),('Switch','SW_SPDT'),('Switch','SW_Push'),('Connector_Generic','Conn_01x02'),('Connector_Generic','Conn_01x06'),('Connector','TestPoint'),('Regulator_Switching','TPS62160DGK'),('RF_Module','ESP32-S3-WROOM-1'),('power','PWR_FLAG')]:load(lib,name)
def pins(key,unit=1):
    out=[]
    for s in children(library[key],'symbol'):
        idx=s[1].rsplit('_',2)[1]
        if idx in ['0',str(unit)]:out+=children(s,'pin')
    return out
def props(key,k):
    return next((n[2] for n in children(library[key],'property') if n[1]==k),'')
PROJECT='YuEEG_8CH_RevA'
rootid=uid(); bom=[]; expected={}; components={}
globals_={'GND','+3V3','+5VA','VBAT_SW','REF_RAW','BIAS_ELECTRODE','BAT_SENSE','UART_TX','UART_RX','ESP_EN','ESP_BOOT'}
globals_.update('AIN'+str(i)+p for i in range(1,9) for p in ['P','N'])
globals_.update('ADS_'+s for s in ['MOSI','MISO','SCLK','CS','DRDY','RESET','PWDN','START'])
class Sheet:
    def __init__(self,name,title,page):
        self.name=name;self.title=title;self.page=page;self.id=uid();self.parts=[];self.used=set();self.symbols=[];self.stubs=set()
    def text(self,t,x,y,size=1.5):self.parts.append(f'(text {q(t)} (at {x} {y} 0) {eff(size,"(justify left top)")} (uuid {q(uid())}))')
    def wire(self,a,b):
        if a==b:return
        self.parts.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {q(uid())}))')
    def label(self,net,x,y,angle=0):
        key=(net,round(x,4),round(y,4))
        if key in self.stubs:return
        self.stubs.add(key)
        typ='global_label' if net in globals_ else 'label';shape='(shape input)' if typ=='global_label' else ''
        direction='right' if angle==0 else 'left'
        justify=f'(justify {direction}'+(' bottom)' if typ=='label' else ')')
        self.parts.append(f'({typ} {q(net)} {shape} (at {x} {y} {angle}) {eff(1.0,justify)} (uuid {q(uid())}))')
    def nc(self,p):self.parts.append(f'(no_connect (at {p[0]} {p[1]}) (uuid {q(uid())}))')
    def junction(self,x,y):self.parts.append(f'(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {q(uid())}))')
    def part(self,key,ref,value,x,y,unit=1,rot=0,footprint=None):
        self.used.add(key); n=library[key];id=components.setdefault((ref,unit),uid()); path=f'/{rootid}/{self.id}'
        fp=footprint if footprint is not None else props(key,'Footprint')
        if footprint is None and key.startswith('Device:'):
            fp={'R':'Resistor_SMD:R_0603_1608Metric','C':'Capacitor_SMD:C_0603_1608Metric','C_Polarized':'Capacitor_SMD:CP_Elec_6.3x7.7','L':'Inductor_SMD:L_4.0x4.0_H1.8','D_Schottky':'Diode_SMD:D_SMA','Fuse':'Fuse:Fuse_1206_3216Metric'}.get(key.split(':')[1],'')
        simple=key.startswith('Device:') or key.startswith('Switch:')
        horizontal=simple and (rot==90 or all(float(sub(p,'at')[3]) in [0,180] for p in pins(key,unit)))
        if horizontal: tx,ty=x,y-6.35
        elif simple:tx,ty=x+5.08,y-2.54
        else:
            allp=pins(key,unit); maxy=max(float(sub(p,'at')[2]) for p in allp);tx,ty=x,y-maxy-12.7
        s=f'(symbol (lib_id {q(key)}) (at {x} {y} {rot}) (unit {unit}) (in_bom yes) (on_board yes) (dnp no) (uuid {q(id)})'
        for k,v,px,py,hidden in [('Reference',ref,tx,ty,False),('Value',value,tx,ty+2.54,False),('Footprint',fp,x,y,True),('Datasheet',props(key,'Datasheet'),x,y,True)]:
            extra='(hide yes)' if hidden else ('(justify left)' if simple and not horizontal else '')
            s+=f'(property {q(k)} {q(v)} (at {px} {py} {rot}) {eff(1.0,extra)})'
        coords={}
        for p in pins(key,unit):
            num=sub(p,'number')[1]; a=sub(p,'at');px,py,ang=map(float,a[1:]);r=math.radians(rot)
            dx=px*math.cos(r)-py*math.sin(r);dy=px*math.sin(r)+py*math.cos(r)
            coords[num]=(round(x+dx,4),round(y-dy,4),(ang+rot)%360)
            s+=f'(pin {q(num)} (uuid {q(uid())}))'
        s+=f'(instances (project {q(PROJECT)} (path {q(path)} (reference {q(ref)}) (unit {unit})))))'
        self.parts.append(s);self.symbols.append((ref,key,unit,coords))
        if not any(b['Reference']==ref for b in bom):bom.append({'Reference':ref,'Value':value,'Footprint':fp,'Sheet':self.name,'Datasheet':props(key,'Datasheet')})
        return coords
    def connect(self,ref,coords,mapping,stub=5.08):
        done=set()
        for num,p in coords.items():
            net=mapping.get(num); xy=p[:2]
            expected[f'{ref}.{num}']=net
            if xy in done:continue
            done.add(xy)
            if net is None:self.nc(xy);continue
            ang=p[2];r=math.radians(ang); end=(round(p[0]-stub*math.cos(r),4),round(p[1]+stub*math.sin(r),4))
            self.wire(xy,end);self.label(net,*end,0 if ang==0 else (180 if ang==180 else 0))
    def named(self,key,ref,value,x,y,mapping,unit=1,rot=0,footprint=None):
        c=self.part(key,ref,value,x,y,unit,rot,footprint);self.connect(ref,c,mapping);return c
    def two(self,kind,ref,value,x,y,a,b,rot=0,footprint=None):return self.named('Device:'+kind,ref,value,x,y,{'1':a,'2':b},rot=rot,footprint=footprint)
    def write(self):
        syms=[]
        for key in sorted(self.used):
            n=library[key].copy();n[1]=key;syms.append(atom(n))
        head=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(uid())}) (paper "A3") (title_block (title {q(self.title)}) (date "2026-10-24") (rev "A0 review") (company "YuEEG") (comment 1 "BATTERY ONLY - NOT VALIDATED FOR HUMAN CONNECTION"))'
        (ROOT/(self.name+'.kicad_sch')).write_text(head+'(lib_symbols '+''.join(syms)+')'+''.join(self.parts)+'(embedded_fonts no))',encoding='utf-8')

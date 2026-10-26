"""Decode the SAME 50-byte frames from USB CDC or Wi-Fi UDP to CSV.
python receive_eeg.py --udp 9000 > samples.csv
python receive_eeg.py --serial COM8 --command start > samples.csv
USB requires pyserial; UDP and protocol tests use only the standard library.
"""
import argparse,binascii,csv,socket,struct,sys
FRAME_SIZE=50
def decode(frame):
    if len(frame)!=50 or frame[:5]!=b'YEEG\x01':raise ValueError('frame/version')
    if binascii.crc_hqx(frame[:48],0xffff)!=int.from_bytes(frame[48:50],'little'):raise ValueError('CRC')
    mode,gain,probe=frame[5:8]
    if mode not in (1,2,3) or gain not in (1,2,4,6,8,12,24):raise ValueError('mode/gain')
    seq,us,missed=struct.unpack_from('<III',frame,8)
    status=int.from_bytes(frame[20:23],'big')
    raw=[int.from_bytes(frame[23+3*i:26+3*i],'big',signed=True) for i in range(8)]
    return {'seq':seq,'device_us':us,'missed_drdy':missed,'mode':mode,'gain':gain,'probe_channel':probe,'status':status,'flags':frame[47],'raw':raw,'uV':[v*4.5e6/(gain*8388608) for v in raw]}
class Decoder:
    def __init__(self):self.buffer=bytearray();self.bad_crc=0
    def feed(self,data):
        self.buffer.extend(data);out=[]
        while True:
            pos=self.buffer.find(b'YEEG')
            if pos<0:self.buffer=self.buffer[-3:];break
            if pos:del self.buffer[:pos]
            if len(self.buffer)<FRAME_SIZE:break
            try:r=decode(bytes(self.buffer[:FRAME_SIZE]))
            except ValueError:self.bad_crc+=1;del self.buffer[0];continue
            out.append(r);del self.buffer[:FRAME_SIZE]
        return out
def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--udp',type=int);g.add_argument('--serial');g.add_argument('--file',help='Rev E raw .yee backup');p.add_argument('--command',default='start');a=p.parse_args()
    if a.file:
        io=open(a.file,'rb');read=lambda:io.read(4096)
    elif a.serial:
        import serial
        io=serial.Serial(a.serial,921600,timeout=.2);io.write((a.command+'\n').encode());read=lambda:io.read(4096)
    else:
        io=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);io.bind(('0.0.0.0',a.udp));read=lambda:io.recvfrom(65535)[0]
    dec=Decoder();w=csv.writer(sys.stdout);w.writerow(['seq','device_us','missed_drdy','mode','gain','probe_channel','status','flags',*[f'ch{i}_uV' for i in range(1,9)]])
    previous=None
    try:
        while True:
            chunk=read()
            if a.file and not chunk:break
            for r in dec.feed(chunk):
                if previous is not None and (r['seq']-previous)&0xffffffff!=1:print(f"sequence gap: {previous}->{r['seq']}",file=sys.stderr)
                previous=r['seq'];w.writerow([r[k] for k in ['seq','device_us','missed_drdy','mode','gain','probe_channel','status','flags']]+r['uV'])
    except KeyboardInterrupt:pass
    finally:io.close()
if __name__=='__main__':main()

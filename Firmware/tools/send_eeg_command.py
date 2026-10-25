"""Authenticated local Wi-Fi control for YuEEG; never touches the serial port."""
import argparse,getpass,socket

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('command',help='Quote multiword commands, e.g. "gain 12" or "udp 192.168.4.2 9000"')
 p.add_argument('--device',default='192.168.4.1');p.add_argument('--port',type=int,default=9001)
 p.add_argument('--token',help='AP password; omitted to enter without terminal echo')
 a=p.parse_args();token=a.token or getpass.getpass('YuEEG AP password: ')
 command=a.command.strip()
 if not command or len(command.encode())>160 or any(c in command for c in '\r\n\x00'):p.error('Invalid command length or control characters')
 payload=f'YEEG {token} {command}'.encode()
 if len(payload)>192:p.error('Packet too long')
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
  s.settimeout(3);s.sendto(payload,(a.device,a.port))
  try:reply,_=s.recvfrom(512)
  except socket.timeout:raise SystemExit('No reply: check device, Wi-Fi, password and power.')
 print(reply.decode(errors='replace'))

if __name__=='__main__':main()

import unittest,struct,binascii
from receive_eeg import decode,Decoder
def frame(values,seq=1,gain=12):
    p=bytearray(b'YEEG'+bytes([1,1,gain,0])+struct.pack('<III',seq,2000,0)+bytes.fromhex('c00000'))
    for v in values:p.extend(v.to_bytes(3,'big',signed=True))
    p.append(0);p.extend(binascii.crc_hqx(p,0xffff).to_bytes(2,'little'));return bytes(p)
class ProtocolTest(unittest.TestCase):
    def test_signed_limits_and_scale(self):
        raw=[-8388608,-1,0,1,8388607,123456,-123456,42];r=decode(frame(raw));self.assertEqual(r['raw'],raw);self.assertEqual(r['uV'][0],-375000)
    def test_fragmented_stream_and_metadata(self):
        d=Decoder();p=frame([0]*8);out=[]
        for v in b'# device ready\n'+p+p:out.extend(d.feed(bytes([v])))
        self.assertEqual(len(out),2)
    def test_crc_corruption_resynchronizes(self):
        p=frame([1]*8);bad=bytearray(p);bad[30]^=4;d=Decoder();self.assertEqual(len(d.feed(bad+p)),1);self.assertGreater(d.bad_crc,0)
    def test_udp_batch(self):self.assertEqual(len(Decoder().feed(b''.join(frame([0]*8,i) for i in range(10)))),10)
    def test_gain(self):self.assertAlmostEqual(decode(frame([12]*8,gain=1))['uV'][0],12*decode(frame([12]*8))['uV'][0])
if __name__=='__main__':unittest.main()

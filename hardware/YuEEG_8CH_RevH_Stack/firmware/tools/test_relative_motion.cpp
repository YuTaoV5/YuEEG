// Runs the exact portable firmware estimator and wire encoder on a host compiler.
#include "../ads1299_driver/YuEEG_RelativeMotion.h"
#include "../ads1299_driver/YuEEG_MotionWire.h"
#include "../ads1299_driver/YuEEG_SafeSpi.h"
#include "../ads1299_driver/YuEEG_MotionGate.h"
#include <cstdio>
#include <cstdlib>
#include <fstream>
using namespace YuEEGMotion;
static int checks=0;
static void require(bool ok,const char* label){++checks;if(!ok){std::fprintf(stderr,"FAIL %s\n",label);std::exit(1);}}
static uint64_t align(Estimator& e,Vec a={0,0,G},Vec bias={},uint64_t start=1000000){
 e.align();for(int i=0;i<=2000;++i)e.update(start+1000*i,bias,a);
 require(e.state().attitude&&e.state().trajectory,"stationary alignment");return start+2000000;
}
int main(int argc,char** argv){
 Estimator e;uint64_t t=align(e);for(int i=1;i<=2000;++i)e.update(t+1000*i,{},{0,0,G});
 require(e.state().position.norm()<1e-8&&e.state().velocity.norm()<1e-8,"rest gravity removal");
 e.reset();t=align(e);for(int i=1;i<=1000;++i)e.update(t+1000*i,{},{1,0,G});
 require(std::fabs(e.state().velocity.x-1)<.001&&std::fabs(e.state().position.x-.5)<.001,"constant acceleration SI integration");
 e.reset();t=align(e);for(int i=1;i<=1000;++i)e.update(t+1000*i,{0,0,90},{0,0,G});
 Vec forward=e.state().q.rotate({1,0,0});require(std::fabs(forward.x)<1e-5&&std::fabs(forward.y-1)<1e-5,"yaw sign and quaternion convention");
 require(e.state().position.norm()<1e-6,"yaw does not create translation");
 e.reset();t=align(e,{0,G*.5,G*std::sqrt(.75)},{.1,-.2,.3});
 for(int i=1;i<=1000;++i)e.update(t+1000*i,{.1,-.2,.3},{0,G*.5,G*std::sqrt(.75)});
 require(e.state().position.norm()<1e-5&&std::fabs(e.state().gyroBias.y+.2)<1e-8,"tilted alignment and gyro bias");
 e.reset();t=align(e);for(int i=1;i<=1000;++i){double yaw=kPi*.5*i/1000.;e.update(t+1000*i,{0,0,90},{std::cos(yaw),-std::sin(yaw),G});}
 require(std::fabs(e.state().position.x-.5)<.001&&std::fabs(e.state().position.y)<.001,"rotating body / world acceleration");
 for(int i=1001;i<=3100;++i)e.update(t+1000*i,{},{0,0,G});
 require(!e.state().trajectory&&e.state().expired&&e.state().attitude,"trajectory expires; attitude continues");
 require(e.state().tiltFeedback,"tilt feedback after trajectory window");
 Vec frozen=e.state().position;e.update(t+3200000,{},{0,0,G});require(e.state().gap&&!e.state().attitude&&!e.state().trajectory,"time gap invalidates solution");
 require((e.state().position-frozen).norm()<1e-12,"no integration across gap");
 e.reset();t=align(e);e.update(t,{},{0,0,G});require(!e.state().attitude,"duplicate timestamp rejected");
 e.reset();t=align(e);e.update(t+1000,{NAN,0,0},{0,0,G});require(!e.state().attitude,"nonfinite sensor rejected");
 e.reset();e.align();for(int i=0;i<=2000;++i)e.update(1000000+1000*i,{3,0,0},{0,0,G});
 require(e.state().alignRejected&&!e.state().attitude,"moving alignment rejected");
 e.reset();e.align();for(int i=0;i<=2000;++i)e.update(1000000+1000*i,{},{(i%2)?.5:-.5,0,G});
 require(e.state().alignRejected,"unstable alignment rejected");
 e.reset();e.align();for(int i=0;i<=2000;++i){e.reject();e.update(1000000+1000*i,{},{0,0,G});}
 require(e.state().alignRejected,"excess rejected samples fail alignment");
 e.reset(123);t=align(e);uint32_t first=e.state().originId;e.align();for(int i=0;i<=2000;++i)e.update(t+1000+1000*i,{},{0,0,G});
 require(e.state().originId==first+1&&e.state().position.norm()==0,"new alignment has new coordinate epoch");
 // Deliberate initial velocity is not observable from a static IMU: no automatic ZUPT.
 e.reset();t=align(e);for(int i=1;i<=1000;++i)e.update(t+1000*i,{},{1,0,G});
 for(int i=1001;i<=2000;++i)e.update(t+1000*i,{},{0,0,G});
 require(e.state().velocity.x>.99&&e.state().position.x>1.49,"no false zero velocity on constant speed");
 MotionFrame f=YuEEGMotionWire::encode(7,t+2000000,SENSOR_VALID,e.state(),{1,2,3},{4,5,G},25.5,11,42,2,3,123,4,15,0);
 require(f.bytes[5]==128&&f.bytes[108]==15&&f.bytes[109]==0,"wire layout");
 require(YuEEGMotionWire::crc(f.bytes,126)==uint16_t(f.bytes[126]|uint16_t(f.bytes[127])<<8),"wire CRC");
 if(argc>1){std::ofstream out(argv[1],std::ios::binary);out.write(reinterpret_cast<const char*>(f.bytes),sizeof(f.bytes));require(out.good(),"write cross-language frame");}
 e.reject();MotionFrame bad=YuEEGMotionWire::encode(8,t+2001000,SENSOR_FAULT,e.state(),{},{},NAN,11,42,3,4,999,4,255,255);
 float invalid;std::memcpy(&invalid,bad.bytes+88,4);require(std::isnan(invalid),"invalid solution serialized asNaN");
 if(argc>2){std::ofstream out(argv[2],std::ios::binary);out.write(reinterpret_cast<const char*>(bad.bytes),sizeof(bad.bytes));require(out.good(),"write invalid-state fixture");}
 AcquisitionGate gate;GateResult gr;
 for(int i=0;i<=21;++i)gr=gate.inspect(true,1,1000000+1350*i,1000250+1350*i,uint8_t(i&15),uint8_t((i+3)&15));
 require(gr.ready&&gate.periodUs()==1350,"learn actual cadence / allow per-group counter offset and wrapping");
 gr=gate.inspect(true,2,1000000+1350*23,1000250+1350*23,7,10);
 require(!gr.ready&&!gr.continuous&&gr.missed==1,"count coincident IRQ/sensor loss once");
 gate.reset();for(int i=0;i<=21;++i)gate.inspect(true,1,1000000+1350*i,1000250+1350*i,uint8_t(i&15),uint8_t(i&15));
 gr=gate.inspect(true,1,1000000+1350*22,1000000+1350*22+1300,6,6);
 require(!gr.valid&&!gr.ready,"late read fails measured-period deadline");
 gr=gate.inspect(false,1,1031050,1031300,7,7);require(!gr.valid&&!gr.ready,"CRC/mixed/edge-crossing failure cannot update filter");
 gate.reset();gr=gate.inspect(true,1,2000,1000,1,1);require(!gr.valid,"reject impossible read timestamp");
 std::printf("PASS %d relative-motion and wire checks (actual firmware core)\n",checks);return 0;
}

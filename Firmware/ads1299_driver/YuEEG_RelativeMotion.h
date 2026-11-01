// Original portable relative-motion core. SI units; right-handed sensor frame.
// Local Z is up; yaw is arbitrary at explicit stationary alignment, not north.
#pragma once
#include <cmath>
#include <cstdint>
namespace YuEEGMotion {
constexpr double G=9.80665, kPi=3.14159265358979323846;
constexpr double TRAJECTORY_SECONDS=3.0, MAX_DT=.020;
struct Vec {
 double x=0,y=0,z=0;
 Vec()=default;
 Vec(double x_,double y_,double z_):x(x_),y(y_),z(z_){}
 Vec operator+(Vec b)const{return {x+b.x,y+b.y,z+b.z};}
 Vec operator-(Vec b)const{return {x-b.x,y-b.y,z-b.z};}
 Vec operator*(double s)const{return {x*s,y*s,z*s};}
 double norm()const{return std::sqrt(x*x+y*y+z*z);}
 bool finite()const{return std::isfinite(x)&&std::isfinite(y)&&std::isfinite(z);}
};
inline Vec cross(Vec a,Vec b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
struct Quat {
 double w=1,x=0,y=0,z=0;
 Quat()=default;
 Quat(double w_,double x_,double y_,double z_):w(w_),x(x_),y(y_),z(z_){}
 Quat operator*(Quat b)const{return {w*b.w-x*b.x-y*b.y-z*b.z,w*b.x+x*b.w+y*b.z-z*b.y,w*b.y-x*b.z+y*b.w+z*b.x,w*b.z+x*b.y-y*b.x+z*b.w};}
 Quat conjugate()const{return {w,-x,-y,-z};}
 bool normalize(){double n=std::sqrt(w*w+x*x+y*y+z*z);if(!std::isfinite(n)||n<1e-12)return false;w/=n;x/=n;y/=n;z/=n;return true;}
 Vec rotate(Vec a)const{Quat r=(*this)*Quat(0,a.x,a.y,a.z)*conjugate();return {r.x,r.y,r.z};}
 static Quat tilt(Vec a){
  double roll=std::atan2(a.y,a.z),pitch=std::atan2(-a.x,std::hypot(a.y,a.z));
  double cr=std::cos(roll/2),sr=std::sin(roll/2),cp=std::cos(pitch/2),sp=std::sin(pitch/2);
  return {cp*cr,cp*sr,sp*cr,-sp*sr}; // yaw=0, body -> local up frame
 }
};
enum Flags:uint16_t {
 SENSOR_VALID=1, ATTITUDE_VALID=2, TRAJECTORY_VALID=4, WARMUP=8,
 YAW_UNREFERENCED=16, POSITION_RELATIVE=32, SAMPLE_GAP=64, ALIGNING=128,
 WINDOW_EXPIRED=256, SENSOR_FAULT=512, EEG_ACTIVE=1024, ALIGN_REJECTED=2048,
 STOPPED=4096, HARDWARE_UNVERIFIED=8192, TILT_FEEDBACK=16384
};
struct State {
 Quat q;Vec velocity,position,gyroBias;
 bool attitude=false,trajectory=false,aligning=false,alignRejected=false,gap=false,expired=false,tiltFeedback=false;
 uint64_t lastUs=0,originUs=0;uint32_t originId=0;
 double age(uint64_t now)const{return originUs&&now>=originUs?double(now-originUs)*1e-6:0;}
 uint16_t flags()const{return YAW_UNREFERENCED|POSITION_RELATIVE|HARDWARE_UNVERIFIED|
  (attitude?ATTITUDE_VALID:0)|(trajectory?TRAJECTORY_VALID:0)|(aligning?ALIGNING:0)|
  (alignRejected?ALIGN_REJECTED:0)|(gap?SAMPLE_GAP:0)|(expired?WINDOW_EXPIRED:0)|(tiltFeedback?TILT_FEEDBACK:0);}
};
class Estimator {
 State s_;Vec sumG_,sumA_,squareG_,squareA_,previousA_;
 uint64_t alignStart_=0;uint32_t samples_=0,rejected_=0;
public:
 const State& state()const{return s_;}
 void reset(uint32_t originSeed=0){s_=State();s_.originId=originSeed;alignStart_=0;samples_=rejected_=0;previousA_={};}
 // Caller explicitly asserts the device will be held stationary; variance checks
 // cannot distinguish stationarity from constant-velocity translation.
 void align(){s_.aligning=true;s_.attitude=s_.trajectory=false;s_.alignRejected=s_.expired=s_.gap=false;s_.tiltFeedback=false;alignStart_=0;samples_=rejected_=0;sumG_=sumA_=squareG_=squareA_={};}
 void reject(){
  if(s_.aligning){++rejected_;return;}
  s_.attitude=s_.trajectory=false;s_.gap=true;s_.tiltFeedback=false;s_.lastUs=0;
 }
 bool update(uint64_t us,Vec gyroDps,Vec acceleration){
  if(!gyroDps.finite()||!acceleration.finite()){reject();return false;}
  if(s_.aligning){
   if(!alignStart_)alignStart_=us;
   if(us<alignStart_){s_.aligning=false;s_.alignRejected=true;return false;}
   ++samples_;sumG_=sumG_+gyroDps;sumA_=sumA_+acceleration;
   squareG_=squareG_+Vec(gyroDps.x*gyroDps.x,gyroDps.y*gyroDps.y,gyroDps.z*gyroDps.z);
   squareA_=squareA_+Vec(acceleration.x*acceleration.x,acceleration.y*acceleration.y,acceleration.z*acceleration.z);
   if(us-alignStart_<2000000)return false;
   Vec mg=sumG_*(1./samples_),ma=sumA_*(1./samples_);
   Vec vg=squareG_*(1./samples_)-Vec(mg.x*mg.x,mg.y*mg.y,mg.z*mg.z);
   Vec va=squareA_*(1./samples_)-Vec(ma.x*ma.x,ma.y*ma.y,ma.z*ma.z);
   s_.aligning=false;
   if(samples_<200||rejected_>samples_/20||mg.norm()>2||std::fabs(ma.norm()-G)>.25||
      vg.x>.04||vg.y>.04||vg.z>.04||va.x>.01||va.y>.01||va.z>.01){s_.alignRejected=true;return false;}
   s_.q=Quat::tilt(ma);s_.gyroBias=mg;s_.velocity=s_.position={};
   s_.originUs=s_.lastUs=us;++s_.originId;s_.attitude=s_.trajectory=true;
   previousA_=s_.q.rotate(ma)-Vec(0,0,G); // no fictitious full accelerometer-bias calibration
   return true;
  }
  if(!s_.attitude)return false;
  if(us<=s_.lastUs){reject();return false;}
  double dt=double(us-s_.lastUs)*1e-6;
  if(dt>MAX_DT){reject();return false;}
  s_.lastUs=us;
  if(s_.age(us)>TRAJECTORY_SECONDS){s_.trajectory=false;s_.expired=true;}
  Vec rate=(gyroDps-s_.gyroBias)*(kPi/180.);
  s_.tiltFeedback=false;
  // During the short trajectory window, gyro-only propagation avoids feeding
  // linear acceleration back into tilt and suppressing the motion being measured.
  if(!s_.trajectory&&std::fabs(acceleration.norm()-G)<.08*G&&gyroDps.norm()<100){
   Vec measured=acceleration*(1./acceleration.norm());
   Vec predicted=s_.q.conjugate().rotate({0,0,1});
   rate=rate+cross(measured,predicted)*.5;s_.tiltFeedback=true;
  }
  Quat dq=s_.q*Quat(0,rate.x,rate.y,rate.z);
  s_.q.w+=.5*dq.w*dt;s_.q.x+=.5*dq.x*dt;s_.q.y+=.5*dq.y*dt;s_.q.z+=.5*dq.z*dt;
  if(!s_.q.normalize()){reject();return false;}
  Vec a=s_.q.rotate(acceleration)-Vec(0,0,G);
  if(s_.trajectory){Vec average=(previousA_+a)*.5;s_.position=s_.position+s_.velocity*dt+average*(.5*dt*dt);s_.velocity=s_.velocity+average*dt;}
  previousA_=a;return true;
 }
};
}

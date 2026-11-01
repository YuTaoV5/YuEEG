#pragma once
#include <cstdint>
#include <cmath>
namespace YuEEGMotion {
struct GateResult {bool valid=false,continuous=false,ready=false;uint32_t missed=0,latencyUs=0;};
class AcquisitionGate {
 bool known_=false;uint8_t rate_=0,acc_=0;uint64_t last_=0;
 double period_=0;uint32_t stable_=0;
public:
 void reset(){known_=false;rate_=acc_=0;last_=0;period_=0;stable_=0;}
 uint32_t stable()const{return stable_;}
 uint32_t periodUs()const{return uint32_t(period_);}
 GateResult inspect(bool checkedFrame,uint32_t edgeDelta,uint64_t edgeUs,uint64_t doneUs,uint8_t rate,uint8_t acc){
  GateResult r;bool timeOk=doneUs>=edgeUs;
  r.latencyUs=timeOk?uint32_t(doneUs-edgeUs):0;
  r.valid=checkedFrame&&timeOk;
  uint8_t rateDelta=uint8_t((rate-rate_)&15),accDelta=uint8_t((acc-acc_)&15);
  r.continuous=edgeDelta==1&&(!known_||(rateDelta==1&&accDelta==1));
  uint32_t edgeLoss=edgeDelta>1?edgeDelta-1:0;
  uint8_t largestDelta=rateDelta>accDelta?rateDelta:accDelta;
  uint32_t counterLoss=r.valid&&known_&&largestDelta>1?largestDelta-1:0;
  // IRQ and sensor counters can describe the same loss; do not count it twice.
  r.missed=edgeLoss>counterLoss?edgeLoss:counterLoss;
  if(r.valid){known_=true;rate_=rate;acc_=acc;}
  double dt=last_&&edgeUs>last_?double(edgeUs-last_):0;last_=edgeUs;
  if(r.valid&&r.continuous&&dt>=100&&dt<=20000){
   if(!period_)period_=dt;
   if(std::fabs(dt-period_)<period_*.2){period_=.95*period_+.05*dt;++stable_;}
   else{stable_=0;period_=dt;}
  }else stable_=0;
  if(period_&&r.latencyUs>=period_*.9){r.valid=false;stable_=0;}
  r.ready=r.valid&&r.continuous&&stable_>=20;return r;
 }
};
}

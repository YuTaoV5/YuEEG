#pragma once
#include "YuEEG_RelativeMotion.h"
#include <cstring>
constexpr size_t MOTION_FRAME_BYTES=128;
struct MotionFrame { uint8_t bytes[MOTION_FRAME_BYTES]; };
namespace YuEEGMotionWire {
inline void u16(uint8_t* p,uint16_t v){p[0]=uint8_t(v);p[1]=uint8_t(v>>8);}
inline void u32(uint8_t* p,uint32_t v){for(int i=0;i<4;++i)p[i]=uint8_t(v>>(8*i));}
inline void u64(uint8_t* p,uint64_t v){for(int i=0;i<8;++i)p[i]=uint8_t(v>>(8*i));}
inline void f32(uint8_t* p,double v){static_assert(sizeof(float)==4,"float32 wire format");float f=float(v);uint32_t bits;std::memcpy(&bits,&f,4);u32(p,bits);}
inline void vec(uint8_t* p,YuEEGMotion::Vec v){f32(p,v.x);f32(p+4,v.y);f32(p+8,v.z);}
inline uint16_t crc(const uint8_t* p,size_t n){uint16_t c=0xffff;while(n--){c^=uint16_t(*p++)<<8;for(int i=0;i<8;++i)c=(c&0x8000)?uint16_t((c<<1)^0x1021):uint16_t(c<<1);}return c;}
inline MotionFrame encode(uint32_t sequence,uint64_t edgeUs,uint16_t extra,
 const YuEEGMotion::State& state,YuEEGMotion::Vec gyro,YuEEGMotion::Vec accel,double temp,
 uint32_t eegSeq,uint32_t eegUs,uint32_t missed,uint32_t rejected,uint32_t latency,uint32_t drops,
 uint8_t rateCounter,uint8_t accCounter){
 using namespace YuEEGMotion;
 MotionFrame f{};uint8_t* p=f.bytes;std::memcpy(p,"YIMU",4);p[4]=1;p[5]=MOTION_FRAME_BYTES;
 u16(p+6,state.flags()|extra);u32(p+8,sequence);u64(p+12,edgeUs);u32(p+20,eegSeq);u32(p+24,eegUs);
 u32(p+28,missed);u32(p+32,rejected);
 Vec invalid{NAN,NAN,NAN};vec(p+36,(extra&SENSOR_VALID)?gyro:invalid);vec(p+48,(extra&SENSOR_VALID)?accel:invalid);
 f32(p+60,state.attitude?state.q.w:NAN);f32(p+64,state.attitude?state.q.x:NAN);f32(p+68,state.attitude?state.q.y:NAN);f32(p+72,state.attitude?state.q.z:NAN);
 vec(p+76,state.trajectory?state.velocity:invalid);vec(p+88,state.trajectory?state.position:invalid);
 f32(p+100,(extra&SENSOR_VALID)?temp:NAN);f32(p+104,state.age(edgeUs));p[108]=rateCounter;p[109]=accCounter;
 u32(p+112,state.originId);u32(p+116,latency);u32(p+120,drops);u16(p+126,crc(p,126));return f;
}
}

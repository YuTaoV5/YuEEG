// SafeSPI bit/word helpers. CRC vectors are from the pinned SCH16T reference.
#pragma once
#include <stdint.h>
namespace YuEEGSafeSpi {
constexpr uint8_t crc8bit(uint64_t data,int bit,uint8_t crc){
 return bit<0?crc:crc8bit(data,bit-1,uint8_t((crc&0x80?uint8_t((crc<<1)^0x2F):uint8_t(crc<<1))^((data>>bit)&1)));
}
constexpr uint8_t crc8(uint64_t frame){return crc8bit(frame&0xFFFFFFFFFF00ULL,47,0xFF);}
constexpr uint8_t crc3bit(uint32_t data,int bit,uint8_t crc){
 return bit<0?crc:crc3bit(data,bit-1,uint8_t(((crc&4?((crc<<1)^3):(crc<<1))^((data>>bit)&1))&7));
}
constexpr uint8_t crc3(uint32_t frame){return crc3bit(frame&0xFFFFFFF8UL,31,5);}
constexpr int32_t signed20(uint64_t frame){return (frame&0x08000000ULL)?int32_t((frame>>8)&0xFFFFF)-0x100000:int32_t((frame>>8)&0xFFFFF);}
// Murata SPI48BF: D47, SA46:37, status36:33, DCNT32:29, reserved28,
// signed sensor27:8, CRC7:0. A counter is an index modulo16, not a timestamp.
constexpr bool sensorData(uint64_t frame){return (frame&(1ULL<<47))!=0;}
constexpr uint8_t counter(uint64_t frame){return uint8_t((frame>>29)&15);}
constexpr bool sameGeneration(uint64_t a,uint64_t b,uint64_t c){return sensorData(a)&&sensorData(b)&&sensorData(c)&&counter(a)==counter(b)&&counter(b)==counter(c);}
constexpr bool oneBitDetect(uint64_t frame,int bit){return bit<8?true:(crc8(frame^(1ULL<<bit))!=uint8_t(frame)&&oneBitDetect(frame,bit-1));}
static_assert(crc8(0x0048000000ACULL)==0xAC,"RATE_X1 CRC");
static_assert(crc8(0x0288000000EFULL)==0xEF,"RATE_X2 CRC");
static_assert(crc8(0x05080000001CULL)==0x1C,"STAT_SUM CRC");
static_assert(crc8(0x0CC80000007CULL)==0x7C,"USER_IF CRC");
static_assert(crc8(0x0DA800000AC3ULL)==0xC3,"RESET CRC");
static_assert(crc3(0x0D60000A)==2,"EN_SENSOR CRC3");
static_assert(crc3(0x0D60001C)==4,"EOI CRC3");
static_assert(crc3(0x00400001)==1,"RATE_X1 CRC3");
static_assert(oneBitDetect(0x0288000000EFULL,47),"Detect every single corrupted payload bit");
static_assert(signed20(0)==0 && signed20(0x07FFFF00)==524287 && signed20(0x08000000)==-524288 && signed20(0x0FFFFF00)==-1,"20-bit signed boundaries");
static_assert(counter(0x8001E0000000ULL)==15 && counter(0x800010000000ULL)==0,"DCNT excludes reserved28");
static_assert(sameGeneration(0x800020000000ULL,0x802020000000ULL,0x804020000000ULL),"Matching generation/address independent");
static_assert(!sameGeneration(0x800020000000ULL,0x802040000000ULL,0x804020000000ULL),"Reject generation crossing");
static_assert(!sameGeneration(0x000020000000ULL,0x802020000000ULL,0x804020000000ULL),"Reject non-sensor reply");
}

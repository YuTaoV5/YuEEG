// Rev E: SDMMC backup and write-only RM67162 QSPI status panel.
// Panel power/logic sequence must be verified on first article, with no electrodes.
#pragma once
#include <SD_MMC.h>
#include <driver/spi_master.h>
#include <esp_heap_caps.h>
#include <freertos/stream_buffer.h>
std::atomic<uint32_t> sdDrops{0},sdFrames{0};
std::atomic<bool> sdReady{false},panelReady{false};
std::atomic<uint32_t> latestSequence{0};
StreamBufferHandle_t backupStream=nullptr;
StaticStreamBuffer_t backupControl;
constexpr size_t BACKUP_BYTES=128*1024;
void backupFrame(const RawFrame& f){
 latestSequence=uint32_t(f.bytes[8])|(uint32_t(f.bytes[9])<<8)|(uint32_t(f.bytes[10])<<16)|(uint32_t(f.bytes[11])<<24);
 if(!sdReady)return;
 if(!backupStream||xStreamBufferSpacesAvailable(backupStream)<FRAME_BYTES){++sdDrops;return;}
 if(xStreamBufferSend(backupStream,f.bytes,FRAME_BYTES,0)!=FRAME_BYTES)++sdDrops;
}
void sdTask(void*){
 // Dedicated SDMMC 1-bit bus; no formatting and no access to ADS SPI2.
 pinMode(48,INPUT);
 if(!SD_MMC.setPins(18,21,47)||!SD_MMC.begin("/sdcard",true,false,20000))vTaskDelete(nullptr);
 File file;uint32_t index=1,lastFlush=millis();uint8_t block[4000];
 sdReady=true;
 for(;;){
  size_t available=xStreamBufferBytesAvailable(backupStream);
  if(available>=sizeof(block)||(!mode&&available)||uint32_t(millis()-lastFlush)>1000){
   size_t take=min(available,sizeof(block));take-=take%FRAME_BYTES;
   if(take){
    if(!file){char name[32];while(index<=999999){snprintf(name,sizeof(name),"/eeg_%06lu.yee",(unsigned long)index++);if(!SD_MMC.exists(name)){file=SD_MMC.open(name,FILE_WRITE);break;}}}
    if(!file){sdReady=false;sdDrops+=take/FRAME_BYTES;break;}
    size_t got=xStreamBufferReceive(backupStream,block,take,0);
    size_t written=file.write(block,got);
    if(written!=got){sdDrops+=(got-written+FRAME_BYTES-1)/FRAME_BYTES;sdReady=false;break;}
    sdFrames+=got/FRAME_BYTES;
   }
   if(uint32_t(millis()-lastFlush)>1000){if(file)file.flush();lastFlush=millis();}
   if(!mode&&!xStreamBufferBytesAvailable(backupStream)&&file){file.flush();file.close();}
  }
  vTaskDelay(pdMS_TO_TICKS(20));
 }
 sdDrops+=xStreamBufferBytesAvailable(backupStream)/FRAME_BYTES;
 if(file)file.close();SD_MMC.end();vTaskDelete(nullptr);
}
spi_device_handle_t panel=nullptr;
bool panelWrite(uint8_t reg,const void* data,size_t bytes,bool quad=false){
 spi_transaction_t t{};t.cmd=quad?0x32:0x02;t.addr=uint32_t(reg)<<8;t.length=bytes*8;t.tx_buffer=data;
 if(quad)t.flags=SPI_TRANS_MODE_QIO;
 return spi_device_polling_transmit(panel,&t)==ESP_OK;
}
bool panelReg(uint8_t reg,uint8_t val){return panelWrite(reg,&val,1);}
bool panelWindow(uint16_t x,uint16_t y,uint16_t w,uint16_t h){
 uint8_t a[]={uint8_t(x>>8),uint8_t(x),uint8_t((x+w-1)>>8),uint8_t(x+w-1)};
 uint8_t c[]={uint8_t(y>>8),uint8_t(y),uint8_t((y+h-1)>>8),uint8_t(y+h-1)};
 return panelWrite(0x2A,a,4)&&panelWrite(0x2B,c,4);
}
// Original compact 3x5 bitmap glyphs. No external font/driver dependency.
uint16_t glyph(char c){
 const char* names="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ:- /";
 static const uint16_t bits[]={0x7B6F,0x2492,0x73E7,0x73CF,0x5BC9,0x79CF,0x79EF,0x7249,0x7BEF,0x7BCF,
 0x2BED,0x6BAE,0x7927,0x6B6E,0x79E7,0x79E4,0x796F,0x5BED,0x7497,0x124F,0x5BAD,0x4927,0x5FED,0x5F6D,0x7B6F,0x7BE4,0x7B7B,0x7BAD,0x79CF,0x7492,0x5B6F,0x5B6A,0x5BFD,0x5AAD,0x5A92,0x72A7,0x0410,0x01C0,0,0x12A4};
 const char* p=strchr(names,c);return p?bits[p-names]:0;
}
bool panelLine(uint16_t y,const char* text,uint16_t* pixels){
 constexpr int scale=3,height=18,width=240;
 memset(pixels,0,width*height*2);
 for(int i=0;text[i]&&i<20;++i){uint16_t g=glyph(text[i]);for(int r=0;r<5;++r)for(int c=0;c<3;++c)if(g&(1<<(14-r*3-c)))
  for(int dy=0;dy<scale;++dy)for(int dx=0;dx<scale;++dx)pixels[(r*scale+dy)*width+i*12+c*scale+dx]=0xFFFF;}
 return panelWindow(0,y,width,height)&&panelWrite(0x2C,pixels,width*height*2,true);
}
void panelTask(void*){
 // Configure every input before turning on the load switch / level translator.
 digitalWrite(42,LOW);pinMode(42,OUTPUT);digitalWrite(17,LOW);pinMode(17,OUTPUT);
 for(int gpio:{2,8,9,14,15,16}){digitalWrite(gpio,gpio==2?HIGH:LOW);pinMode(gpio,OUTPUT);}
 spi_bus_config_t bus{};bus.sclk_io_num=8;bus.mosi_io_num=9;bus.miso_io_num=14;bus.quadwp_io_num=15;bus.quadhd_io_num=16;bus.max_transfer_sz=240*18*2;bus.flags=SPICOMMON_BUSFLAG_MASTER|SPICOMMON_BUSFLAG_QUAD;
 spi_device_interface_config_t dev{};dev.clock_speed_hz=10000000;dev.mode=0;dev.spics_io_num=2;dev.queue_size=1;dev.command_bits=8;dev.address_bits=24;dev.flags=SPI_DEVICE_HALFDUPLEX;
 uint16_t* pixels=(uint16_t*)heap_caps_malloc(240*18*2,MALLOC_CAP_DMA|MALLOC_CAP_INTERNAL);
 if(!pixels||spi_bus_initialize(SPI3_HOST,&bus,SPI_DMA_CH_AUTO)!=ESP_OK||spi_bus_add_device(SPI3_HOST,&dev,&panel)!=ESP_OK){if(pixels)free(pixels);vTaskDelete(nullptr);}
 digitalWrite(42,HIGH);vTaskDelay(pdMS_TO_TICKS(20));digitalWrite(17,HIGH);vTaskDelay(pdMS_TO_TICKS(120));
 bool ok=panelWrite(0x11,nullptr,0);vTaskDelay(pdMS_TO_TICKS(120));
 ok=ok&&panelReg(0x3A,0x55)&&panelReg(0x36,0)&&panelReg(0x51,0x40);
 memset(pixels,0,240*18*2);
 for(int y=0;ok&&y<536;y+=18){int h=min(18,536-y);ok=panelWindow(0,y,240,h)&&panelWrite(0x2C,pixels,240*h*2,true);}
 ok=ok&&panelWrite(0x29,nullptr,0);panelReady=ok;
 while(ok){char text[24];
  ok=panelLine(24,"YUEEG REV E",pixels);
  snprintf(text,sizeof(text),"ADC %s MODE %u",adcOK?"OK":"FAULT",mode.load());ok=ok&&panelLine(72,text,pixels);
  snprintf(text,sizeof(text),"SEQ %lu",(unsigned long)latestSequence.load());ok=ok&&panelLine(108,text,pixels);
  snprintf(text,sizeof(text),"WIFI %u USB %u",WiFi.softAPgetStationNum(),bool(Serial));ok=ok&&panelLine(144,text,pixels);
  snprintf(text,sizeof(text),"SD %s",sdReady?"READY":"ABSENT / FAULT");ok=ok&&panelLine(180,text,pixels);
  snprintf(text,sizeof(text),"SAVED %lu",(unsigned long)sdFrames.load());ok=ok&&panelLine(216,text,pixels);
  snprintf(text,sizeof(text),"SD DROP %lu",(unsigned long)sdDrops.load());ok=ok&&panelLine(252,text,pixels);
  snprintf(text,sizeof(text),"ADC MISS %lu",(unsigned long)missed.load());ok=ok&&panelLine(288,text,pixels);
  ok=ok&&panelLine(360,"REC START / STOP",pixels);vTaskDelay(pdMS_TO_TICKS(1000));
 }
 panelReady=false;digitalWrite(42,LOW);free(pixels);vTaskDelete(nullptr);
}
void startUI(){
 pinMode(41,INPUT);
 auto* memory=(uint8_t*)heap_caps_malloc(BACKUP_BYTES+1,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
 if(memory)backupStream=xStreamBufferCreateStatic(BACKUP_BYTES,FRAME_BYTES,memory,&backupControl);
 if(backupStream)xTaskCreatePinnedToCore(sdTask,"sd_backup",6144,nullptr,1,nullptr,0);
 xTaskCreatePinnedToCore(panelTask,"amoled",4096,nullptr,1,nullptr,0);
}
void pollRecButton(){
 static bool last=HIGH,stable=HIGH;static uint32_t changed=0;bool now=digitalRead(41);
 if(now!=last){last=now;changed=millis();}
 if(now!=stable&&uint32_t(millis()-changed)>30){stable=now;if(!stable){if(mode)stopADC();else configureADC(1);}}
}

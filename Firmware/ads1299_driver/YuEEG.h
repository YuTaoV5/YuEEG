// ESP32-S3-WROOM-1U-N16R8, YuEEG Rev H development, NP-BX1 battery.
#pragma once
#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Preferences.h>
#include <esp_system.h>
#include <atomic>
constexpr uint8_t CS=10,SCLK_GPIO=12,MOSI_GPIO=11,MISO_GPIO=13;
constexpr uint8_t DRDY=4,ADS_RESET=5,PWDN=6,ADS_START=7,FRAME_BYTES=50;
struct RawFrame { uint8_t bytes[FRAME_BYTES]; };
QueueHandle_t outputQueue;
struct ControlCommand { char text[161]; };
QueueHandle_t controlQueue;
TaskHandle_t acquisitionTask=nullptr;
portMUX_TYPE irqMux=portMUX_INITIALIZER_UNLOCKED,targetMux=portMUX_INITIALIZER_UNLOCKED;
volatile uint32_t pending=0,lastEdgeUs=0;
uint32_t sequence=0;
std::atomic<uint32_t> missed{0};
std::atomic<uint32_t> queueDrops{0},usbDrops{0},udpDrops{0};
std::atomic<uint8_t> mode{0};
uint8_t gain=12,testChannel=0; // 0 stopped;1 EEG;2 internal test;3 electrode probe
std::atomic<bool> adcOK{false};
constexpr uint8_t LED_RUN=38,LED_WIFI=39,LED_FAULT=40; // active low, 2.2k series, no PWM
#include "YuEEG_Battery.h"
Preferences prefs;
String commandLine;
String apToken; // immutable after Wi-Fi setup, also authenticates local UDP control
IPAddress udpAddress(192,168,4,255);
uint16_t udpPort=9000;
void IRAM_ATTR onDRDY() {
 portENTER_CRITICAL_ISR(&irqMux);++pending;lastEdgeUs=micros();portEXIT_CRITICAL_ISR(&irqMux);
 BaseType_t wake=pdFALSE;vTaskNotifyGiveFromISR(acquisitionTask,&wake);if(wake)portYIELD_FROM_ISR();
}
void adcCommand(uint8_t cmd) {
 SPI.beginTransaction(SPISettings(2000000,MSBFIRST,SPI_MODE1));
 digitalWrite(CS,LOW);SPI.transfer(cmd);digitalWrite(CS,HIGH);SPI.endTransaction();delayMicroseconds(4);
}
void regWrite(uint8_t reg,uint8_t value) {
 SPI.beginTransaction(SPISettings(2000000,MSBFIRST,SPI_MODE1));
 digitalWrite(CS,LOW);SPI.transfer(0x40|reg);delayMicroseconds(4);SPI.transfer(0);delayMicroseconds(4);
 SPI.transfer(value);digitalWrite(CS,HIGH);SPI.endTransaction();delayMicroseconds(4);
}
uint8_t regRead(uint8_t reg) {
 SPI.beginTransaction(SPISettings(2000000,MSBFIRST,SPI_MODE1));
 digitalWrite(CS,LOW);SPI.transfer(0x20|reg);delayMicroseconds(4);SPI.transfer(0);delayMicroseconds(4);
 uint8_t v=SPI.transfer(0);digitalWrite(CS,HIGH);SPI.endTransaction();delayMicroseconds(4);return v;
}
uint8_t gainBits() {
 switch(gain){case 1:return 0;case 2:return 0x10;case 4:return 0x20;case 6:return 0x30;case 8:return 0x40;case 12:return 0x50;default:return 0x60;}
}
void stopADC() {
 digitalWrite(ADS_START,LOW);adcCommand(0x0A);adcCommand(0x11);mode=0;
 portENTER_CRITICAL(&irqMux);pending=0;portEXIT_CRITICAL(&irqMux);
}
bool checkedWrite(uint8_t reg,uint8_t value){
 regWrite(reg,value);
 // CONFIG3 bit0 is live BIAS_STAT, not a writable configuration bit.
 uint8_t mask=reg==3?0xFE:0xFF;return (regRead(reg)&mask)==(value&mask);
}
bool configureADC(uint8_t requested,uint8_t electrode=0) {
 if(!adcOK)return false;stopADC();bool ok=true;
 ok&=checkedWrite(1,0x95);ok&=checkedWrite(2,requested==2?0xD1:0xC0);ok&=checkedWrite(3,0xEC);
 ok&=checkedWrite(4,requested==3?0x02:0); // 6nA, 31.25Hz periodic, NOT 0x06 (=24nA)
 for(uint8_t i=0;i<8;++i)ok&=checkedWrite(5+i,gainBits()|(requested==2?5:0));
 ok&=checkedWrite(0x0D,requested==2?0:0xFF);ok&=checkedWrite(0x0E,0);
 ok&=checkedWrite(0x0F,requested==3?(1U<<electrode):0);ok&=checkedWrite(0x10,0);ok&=checkedWrite(0x11,0);
 ok&=checkedWrite(0x15,0); // external REF routing, unused SRB1/SRB2
 if(!ok){digitalWrite(PWDN,LOW);adcOK=false;return false;}
 delay(500); // internal reference settling, verify on bench
 mode=requested;testChannel=electrode;
 portENTER_CRITICAL(&irqMux);pending=0;portEXIT_CRITICAL(&irqMux);
 adcCommand(0x10);digitalWrite(ADS_START,HIGH);return true;
}
void put32(uint8_t* p,uint32_t v){for(int i=0;i<4;++i)p[i]=v>>(8*i);}
uint16_t crc16(const uint8_t* p,size_t n) {
 uint16_t crc=0xFFFF;while(n--){crc^=uint16_t(*p++)<<8;for(int i=0;i<8;++i)crc=(crc&0x8000)?(crc<<1)^0x1021:crc<<1;}return crc;
}
void capture() {
 uint32_t n,stamp;portENTER_CRITICAL(&irqMux);n=pending;stamp=lastEdgeUs;pending=0;portEXIT_CRITICAL(&irqMux);
 if(!n||!mode)return;missed+=n-1;sequence+=n-1;RawFrame f{};memcpy(f.bytes,"YEEG",4);
 f.bytes[4]=1;f.bytes[5]=mode;f.bytes[6]=gain;f.bytes[7]=mode==3?testChannel+1:0;
 put32(f.bytes+8,sequence++);put32(f.bytes+12,stamp);put32(f.bytes+16,missed);
 SPI.beginTransaction(SPISettings(2000000,MSBFIRST,SPI_MODE1));digitalWrite(CS,LOW);
 for(int i=0;i<27;++i)f.bytes[20+i]=SPI.transfer(0);digitalWrite(CS,HIGH);SPI.endTransaction();
 f.bytes[47]=(f.bytes[20]&0xF0)==0xC0?0:1;
 uint16_t c=crc16(f.bytes,48);f.bytes[48]=c;f.bytes[49]=c>>8;
 if(xQueueSend(outputQueue,&f,0)!=pdTRUE)++queueDrops;
}
#include "YuEEG_UI.h"
void receiveControl(WiFiUDP& udp) {
 int size=udp.parsePacket();if(size<=0)return;
 IPAddress source=udp.remoteIP();uint16_t port=udp.remotePort();
 char packet[193];int n=udp.read(packet,sizeof(packet)-1);udp.flush();
 if(size>192||n<=0)return;packet[n]=0;
 String text(packet),prefix="YEEG "+apToken+" ";if(!text.startsWith(prefix))return;
 String cmd=text.substring(prefix.length());cmd.trim();if(cmd.length()>160)return;String reply;
 if(cmd=="status"){
  char status[160],battery[40];batteryText(battery,sizeof(battery));snprintf(status,sizeof(status),"# ADC=%s mode=%u missed=%lu queue_drop=%lu usb_drop=%lu udp_drop=%lu",adcOK?"ready":"FAULT",mode.load(),(unsigned long)missed.load(),(unsigned long)queueDrops.load(),(unsigned long)usbDrops.load(),(unsigned long)udpDrops.load());reply=String(status)+"\n# "+battery;
 }else if(cmd=="start"||cmd=="stop"||cmd=="test"||cmd.startsWith("probe ")||cmd.startsWith("gain ")||cmd.startsWith("udp ")){
  ControlCommand c{};cmd.toCharArray(c.text,sizeof(c.text));reply=xQueueSend(controlQueue,&c,0)==pdTRUE?"# queued; query status to confirm":"# busy";
 }else reply="# rejected";
 if(udp.beginPacket(source,port)){udp.write((const uint8_t*)reply.c_str(),reply.length());udp.endPacket();}
}
void outputTask(void*) {
 WiFiUDP udp;udp.begin(9001);uint8_t batch[FRAME_BYTES*10];size_t count=0;uint32_t firstMs=0;
 for(;;){RawFrame f;
  if(xQueueReceive(outputQueue,&f,pdMS_TO_TICKS(5))==pdTRUE){
   backupFrame(f);
   if(Serial&&Serial.availableForWrite()>=FRAME_BYTES){if(Serial.write(f.bytes,FRAME_BYTES)!=FRAME_BYTES)++usbDrops;}else ++usbDrops;
   if(!count)firstMs=millis();memcpy(batch+count*FRAME_BYTES,f.bytes,FRAME_BYTES);++count;
  }
  if(count&&(count==10||uint32_t(millis()-firstMs)>=20)){
   IPAddress target;uint16_t port;portENTER_CRITICAL(&targetMux);target=udpAddress;port=udpPort;portEXIT_CRITICAL(&targetMux);
   if(udp.beginPacket(target,port)){udp.write(batch,count*FRAME_BYTES);if(!udp.endPacket())udpDrops+=count;}else udpDrops+=count;
   count=0;
  }
  receiveControl(udp); // enqueue only; all ADC/SPI configuration stays in loop task
  bool blink=(millis()/500)&1;
  digitalWrite(LED_RUN,mode?(!blink):HIGH);
  digitalWrite(LED_WIFI,(WiFi.softAPgetStationNum()||WiFi.status()==WL_CONNECTED)?LOW:!blink);
  digitalWrite(LED_FAULT,(!adcOK||queueDrops.load()||missed||batteryLow())?LOW:HIGH);
 }
}
void startWiFi() {
 prefs.begin("yueeg",false);String pass=prefs.getString("ap_pass","");
 if(pass.length()<12){static const char a[]="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
  for(int i=0;i<16;++i)pass+=a[esp_random()%(sizeof(a)-1)];prefs.putString("ap_pass",pass);}
 String name="YuEEG-"+String(uint32_t(ESP.getEfuseMac()),HEX);
 apToken=pass;
 WiFi.mode(WIFI_AP_STA);WiFi.setSleep(false);WiFi.softAP(name.c_str(),pass.c_str(),6,false,2);
 String ssid=prefs.getString("ssid","");if(ssid.length())WiFi.begin(ssid.c_str(),prefs.getString("pass","").c_str());
}
void report() {
 Serial.printf("# YuEEG v1 ADC=%s mode=%u gain=%u missed=%lu queue_drop=%lu usb_drop=%lu udp_drop=%lu\n",adcOK?"ready":"FAULT",mode.load(),gain,(unsigned long)missed.load(),(unsigned long)queueDrops.load(),(unsigned long)usbDrops.load(),(unsigned long)udpDrops.load());
 Serial.printf("# RevH SD=%s saved=%lu sd_drop=%lu panel_bus=%s\n",sdReady?"ready":"absent/fault",(unsigned long)sdFrames.load(),(unsigned long)sdDrops.load(),panelReady?"OK (unverified panel)":"not ready");
 char battery[40];batteryText(battery,sizeof(battery));Serial.printf("# %s (protected loaded supply; nominal divider, bench calibration pending)\n",battery);
 Serial.printf("# AP %s password=%s IP=%s STA=%s\n",WiFi.softAPSSID().c_str(),prefs.getString("ap_pass","").c_str(),WiFi.softAPIP().toString().c_str(),WiFi.localIP().toString().c_str());
 Serial.printf("# CPU=%uMHz Flash=%lu PSRAM=%lu bytes\n",ESP.getCpuFreqMHz(),(unsigned long)ESP.getFlashChipSize(),(unsigned long)ESP.getPsramSize());
 Serial.println("# start | stop | test | probe 1..8 | gain 1/2/4/6/8/12/24 | udp IP PORT | wifi SSID<TAB>PASSWORD | status");
 Serial.println("# Probe returns excited-loop data, not calibrated independent electrode impedance. UDP default 192.168.4.255:9000.");
}
void handleCommand(String cmd) {
 cmd.trim();
 if(cmd=="start"||cmd=="1")configureADC(1);
 else if(cmd=="stop"||cmd=="0")stopADC();
 else if(cmd=="test"||cmd=="3")configureADC(2);
 else if(cmd.startsWith("probe ")){int c=cmd.substring(6).toInt();if(c>=1&&c<=8)configureADC(3,c-1);}
 else if(cmd.startsWith("gain ")){int g=cmd.substring(5).toInt();if(g==1||g==2||g==4||g==6||g==8||g==12||g==24){uint8_t old=mode;stopADC();gain=g;if(old)configureADC(old,testChannel);}}
 else if(cmd.startsWith("udp ")){int s=cmd.indexOf(' ',4);IPAddress ip;long port=cmd.substring(s+1).toInt();if(s>4&&ip.fromString(cmd.substring(4,s))&&port>0&&port<=65535){portENTER_CRITICAL(&targetMux);udpAddress=ip;udpPort=port;portEXIT_CRITICAL(&targetMux);}}
 else if(cmd.startsWith("wifi ")){int s=cmd.indexOf('\t',5);if(s>5){String ssid=cmd.substring(5,s),pass=cmd.substring(s+1);prefs.putString("ssid",ssid);prefs.putString("pass",pass);WiFi.begin(ssid.c_str(),pass.c_str());}}
 else if(cmd=="status"||cmd=="?")report();
}
void setup() {
 acquisitionTask=xTaskGetCurrentTaskHandle();
 for(uint8_t led:{LED_RUN,LED_WIFI,LED_FAULT}){pinMode(led,OUTPUT);digitalWrite(led,HIGH);}
 pinMode(PWDN,OUTPUT);digitalWrite(PWDN,LOW);pinMode(ADS_RESET,OUTPUT);digitalWrite(ADS_RESET,LOW);
 pinMode(ADS_START,OUTPUT);digitalWrite(ADS_START,LOW);pinMode(CS,OUTPUT);digitalWrite(CS,HIGH);
 pinMode(DRDY,INPUT);SPI.begin(SCLK_GPIO,MISO_GPIO,MOSI_GPIO,CS);Serial.begin(921600);Serial.setTxTimeoutMs(0);
 outputQueue=xQueueCreate(128,sizeof(RawFrame));controlQueue=xQueueCreate(4,sizeof(ControlCommand));if(!outputQueue||!controlQueue){digitalWrite(LED_FAULT,LOW);while(true)delay(1000);}
 delay(500);digitalWrite(PWDN,HIGH);delay(10000); // verify VCAP1-AVSS>1.1V; no rail fault monitor
 digitalWrite(ADS_RESET,HIGH);delay(1);adcCommand(0x11);uint8_t id=regRead(0);adcOK=(id&0x1F)==0x1E;
 startBatteryMonitor();startWiFi();startUI();xTaskCreatePinnedToCore(outputTask,"eeg_output",6144,nullptr,2,nullptr,0);
 attachInterrupt(digitalPinToInterrupt(DRDY),onDRDY,FALLING);report(); // stopped until host command
}
void loop() {
 ControlCommand remote;if(xQueueReceive(controlQueue,&remote,0)==pdTRUE)handleCommand(String(remote.text));
 pollRecButton();capture();if(Serial.available()){char c=Serial.read();if(c=='\n'){handleCommand(commandLine);commandLine="";}else if(c!='\r'){if(commandLine.length()<160)commandLine+=c;else commandLine="";}}
 // Sleep until DRDY or 1ms timeout for commands; ISR wakes the task immediately.
 ulTaskNotifyTake(pdTRUE,pdMS_TO_TICKS(1));
}

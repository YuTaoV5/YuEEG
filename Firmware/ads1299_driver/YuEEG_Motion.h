// Single-owner SCH16T task: DRDY -> checked burst -> relative estimator -> queues.
#pragma once
#include "YuEEG_SCH16T.h"
#include "YuEEG_MotionWire.h"
#include "YuEEG_MotionGate.h"
#include <esp_timer.h>
enum class MotionCommand:uint8_t {Start,Stop,Align,Probe,Status};
struct MotionText {char text[192];};
QueueHandle_t motionOutputQueue=nullptr,motionControlQueue=nullptr,motionTextQueue=nullptr;
TaskHandle_t motionTaskHandle=nullptr;
std::atomic<uint32_t> motionDrops{0},motionUsbDrops{0},motionUdpDrops{0},motionRejected{0},motionMissed{0},motionPeriodUs{0},motionMaxLatencyUs{0};
portMUX_TYPE motionIrqMux=portMUX_INITIALIZER_UNLOCKED;
volatile uint32_t motionEdges=0;
volatile int64_t motionEdgeUs=0;
void IRAM_ATTR onMotionDRDY(){
 portENTER_CRITICAL_ISR(&motionIrqMux);++motionEdges;motionEdgeUs=esp_timer_get_time();portEXIT_CRITICAL_ISR(&motionIrqMux);
 BaseType_t wake=pdFALSE;vTaskNotifyGiveFromISR(motionTaskHandle,&wake);if(wake)portYIELD_FROM_ISR();
}
struct MotionEdge {uint32_t count;uint64_t us;};
MotionEdge motionEdge(){MotionEdge e;portENTER_CRITICAL(&motionIrqMux);e.count=motionEdges;e.us=uint64_t(motionEdgeUs);portEXIT_CRITICAL(&motionIrqMux);return e;}
void motionNote(const char* message){MotionText t{};strncpy(t.text,message,sizeof(t.text)-1);if(motionTextQueue)xQueueSend(motionTextQueue,&t,0);}
void motionStatus(){
 char line[192];snprintf(line,sizeof(line),"# IMU running=%u flags=%u period_us=%lu rejected=%lu missed=%lu queue_drop=%lu usb_drop=%lu udp_drop=%lu sd_drop=%lu\n",imuRunning.load(),currentMotionFlags(),(unsigned long)motionPeriodUs.load(),(unsigned long)motionRejected.load(),(unsigned long)motionMissed.load(),(unsigned long)motionDrops.load(),(unsigned long)motionUsbDrops.load(),(unsigned long)motionUdpDrops.load(),(unsigned long)sdMotionDrops.load());motionNote(line);
}
bool queueMotion(MotionCommand c){
 if(!motionControlQueue||!motionTaskHandle||xQueueSend(motionControlQueue,&c,0)!=pdTRUE){motionNote("# IMU command unavailable / busy\n");return false;}
 xTaskNotifyGive(motionTaskHandle);return true;
}
void motionTask(void*){
 using namespace YuEEGMotion;
 spi_device_handle_t device=nullptr;
 spi_device_interface_config_t cfg{};cfg.clock_speed_hz=2000000;cfg.mode=0;cfg.spics_io_num=SPI3_IMU_CS;cfg.queue_size=1;
 if(!beginSharedSpi3()||!attachSharedSpi3(cfg,&device)){
  motionFlags=SENSOR_FAULT|STOPPED|HARDWARE_UNVERIFIED|YAW_UNREFERENCED|POSITION_RELATIVE;
  motionNote("# IMU SPI3 attach failed\n");motionTaskHandle=nullptr;vTaskDelete(nullptr);return;
 }
 SCH16T_K01 sensor(device,SPI3_IMU_CS,-1,0);Estimator estimator;estimator.reset(esp_random());
 uint32_t seq=0,processed=0;uint64_t lastPublish=0,thermalStart=0;AcquisitionGate gate;
 auto emit=[&](uint64_t us,uint16_t extra,Vec gyro,Vec acc,double temp,uint8_t rc,uint8_t ac,uint32_t latency){
  if(thermalStart&&us-thermalStart<900000000ULL)extra|=WARMUP;
  uint32_t eegSeq,eegUs;portENTER_CRITICAL(&irqMux);eegSeq=motionEegSeq;eegUs=motionEegUs;portEXIT_CRITICAL(&irqMux);
  if(mode.load())extra|=EEG_ACTIVE;
  motionFlags=estimator.state().flags()|extra;
  motionLastPublishMs=millis();
  MotionFrame f=YuEEGMotionWire::encode(seq++,us,extra,estimator.state(),gyro,acc,temp,eegSeq,eegUs,motionMissed.load(),motionRejected.load(),latency,motionDrops.load(),rc,ac);
  if(xQueueSend(motionOutputQueue,&f,0)!=pdTRUE)++motionDrops;
  lastPublish=us;
 };
 pinMode(IMU_DRDY_GPIO,INPUT);
 for(;;){
  MotionCommand cmd;
  while(xQueueReceive(motionControlQueue,&cmd,0)==pdTRUE){
   if(cmd==MotionCommand::Status){motionStatus();continue;}
   if(cmd==MotionCommand::Stop){
    detachInterrupt(digitalPinToInterrupt(IMU_DRDY_GPIO));imuRunning=false;estimator.reset(estimator.state().originId);
    emit(esp_timer_get_time(),STOPPED,{},{},NAN,255,255,0);motionNote("# IMU stopped\n");continue;
   }
   if(cmd==MotionCommand::Align){
    if(!imuRunning||gate.stable()<20){motionNote("# IMU start and wait for stable DRDY timing before align\n");continue;}
    estimator.align();motionNote("# IMU hold stationary >=2s; yaw/origin reset on accepted alignment\n");continue;
   }
   if(imuRunning){motionNote("# IMU already running; stop before restart / probe\n");continue;}
   if(mode.load()!=0){motionNote("# Stop EEG before IMU initialization / probe\n");continue;}
   bool streaming=cmd==MotionCommand::Start;
   const int result=sensor.begin({68,68,68},{1600,1600,3200,3200,3200},{32,32},streaming);
   if(result!=SCH16T_OK){estimator.reject();emit(esp_timer_get_time(),SENSOR_FAULT|STOPPED,{},{},NAN,255,255,0);motionNote("# IMU initialization failed; no valid solution\n");continue;}
   // IDF4.4 requires portMAX_DELAY; freshness is checked after acquisition.
   if(spi_device_acquire_bus(device,portMAX_DELAY)!=ESP_OK){motionNote("# IMU bus acquire failed\n");continue;}
   SCH16T_raw_data raw{};sensor.getDataDecimated(&raw);spi_device_release_bus(device);
   if(!streaming){
    bool good=!raw.frame_error&&sensor.transportHealthy()&&raw.generation_consistent;
    SCH16T_result sample{};if(good)sensor.convertDataDecimated(&raw,&sample);
    char line[192];if(good)snprintf(line,sizeof(line),"# IMU probe gyro_dps=%.5f,%.5f,%.5f acc_mps2=%.5f,%.5f,%.5f temp_C=%.2f; unverified\n",sample.Rate2[0],sample.Rate2[1],sample.Rate2[2],sample.Acc2[0],sample.Acc2[1],sample.Acc2[2],sample.Temp);
    else snprintf(line,sizeof(line),"# IMU probe invalid frame / mixed generation\n");motionNote(line);continue;
   }
   estimator.reset(estimator.state().originId);gate.reset();motionPeriodUs=0;
   thermalStart=esp_timer_get_time();motionLastPublishMs=millis();imuRunning=true;processed=motionEdge().count;
   attachInterrupt(digitalPinToInterrupt(IMU_DRDY_GPIO),onMotionDRDY,RISING);
   motionNote("# IMU streaming YIMU/128: USB + UDP9002 + SD .yim; send imu align while stationary\n");
  }
  if(!imuRunning){ulTaskNotifyTake(pdTRUE,pdMS_TO_TICKS(100));continue;}
  MotionEdge edge=motionEdge();
  if(edge.count==processed){
   if(ulTaskNotifyTake(pdTRUE,pdMS_TO_TICKS(100))==0){
    estimator.reject();++motionRejected;gate.reset();motionPeriodUs=0;
    emit(esp_timer_get_time(),SENSOR_FAULT,{},{},NAN,255,255,0);
    // DRY can remain asserted if an initial edge was missed. Drain it, do not
    // invent a sensor timestamp; then wait for an actual subsequent edge.
    if(digitalRead(IMU_DRDY_GPIO)&&spi_device_acquire_bus(device,portMAX_DELAY)==ESP_OK){SCH16T_raw_data discarded{};sensor.getDataDecimated(&discarded);spi_device_release_bus(device);processed=motionEdge().count;}
   }
   continue;
  }
  if(spi_device_acquire_bus(device,portMAX_DELAY)!=ESP_OK){estimator.reject();++motionRejected;continue;}
  edge=motionEdge(); // bus wait may span samples; use the newest actual ISR edge
  uint32_t skipped=edge.count-processed;processed=edge.count;
  SCH16T_raw_data raw{};sensor.getDataDecimated(&raw);uint64_t done=esp_timer_get_time();MotionEdge after=motionEdge();spi_device_release_bus(device);
  GateResult checked=gate.inspect(!raw.frame_error&&sensor.transportHealthy()&&raw.generation_consistent&&after.count==edge.count,skipped,edge.us,done,raw.Rate2_counter[0],raw.Acc2_counter[0]);
  uint32_t latency=checked.latencyUs;if(latency>motionMaxLatencyUs.load())motionMaxLatencyUs=latency;
  bool good=checked.valid;motionMissed+=checked.missed;motionPeriodUs=gate.periodUs();
  SCH16T_result sample{};Vec gyro{},acc{};
  if(good){sensor.convertDataDecimated(&raw,&sample);gyro={sample.Rate2[0],sample.Rate2[1],sample.Rate2[2]};acc={sample.Acc2[0],sample.Acc2[1],sample.Acc2[2]};}
  if(!good||!checked.continuous||(!checked.ready&&(estimator.state().attitude||estimator.state().aligning))){estimator.reject();++motionRejected;}
  else if(checked.ready)estimator.update(edge.us,gyro,acc);
  // Publish ~50Hz while integrating every accepted sensor sample. Output I/O
  // and SD operations never execute in this task or either DRDY ISR.
  if(edge.us-lastPublish>=20000){emit(edge.us,good?SENSOR_VALID:SENSOR_FAULT,gyro,acc,sample.Temp,good?raw.Rate2_counter[0]:255,good?raw.Acc2_counter[0]:255,latency);}
 }
}
void startMotionRuntime(){
 motionOutputQueue=xQueueCreate(16,sizeof(MotionFrame));motionControlQueue=xQueueCreate(8,sizeof(MotionCommand));motionTextQueue=xQueueCreate(4,sizeof(MotionText));
 if(!motionOutputQueue||!motionControlQueue||!motionTextQueue||xTaskCreatePinnedToCore(motionTask,"imu",8192,nullptr,3,&motionTaskHandle,0)!=pdPASS){motionFlags=YuEEGMotion::STOPPED|YuEEGMotion::SENSOR_FAULT|YuEEGMotion::HARDWARE_UNVERIFIED;}
}

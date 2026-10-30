// Rev H only: protected NP-BX1 voltage, before the 5V boost converter.
// This is loaded supply voltage, not open-circuit cell voltage or state of charge.
#pragma once
constexpr uint8_t BATTERY_ADC_GPIO=1; // ESP32-S3 ADC1_CH0, U2 pad 39
constexpr uint32_t BATTERY_STATE_VALID=1UL<<31, BATTERY_STATE_LOW=1UL<<30;
constexpr uint16_t BATTERY_LOW_ON_MV=3450, BATTERY_LOW_OFF_MV=3550;
constexpr uint32_t BATTERY_DIVIDER_TOP_OHMS=330000, BATTERY_DIVIDER_BOTTOM_OHMS=100000;
// R309=330k, R310=100k; nominal divider ratio 4.3. Board calibration is pending.
std::atomic<uint32_t> batteryState{0};
bool batteryLow(){return (batteryState.load()&BATTERY_STATE_LOW)!=0;}
void batteryText(char* text,size_t size){
 const uint32_t state=batteryState.load();
 if(!(state&BATTERY_STATE_VALID)){snprintf(text,size,"CELL UNAVAILABLE");return;}
 snprintf(text,size,"CELL %u MV %s",unsigned(state&0xFFFF),state&BATTERY_STATE_LOW?"LOW":"OK");
}
void batteryTask(void*){
 pinMode(BATTERY_ADC_GPIO,INPUT);
 // ADC1 remains usable with Wi-Fi. This attenuation leaves margin above .977V.
 analogSetPinAttenuation(BATTERY_ADC_GPIO,ADC_2_5db);
 TickType_t wake=xTaskGetTickCount();bool low=false;
 for(;;){
  uint32_t sum=0,least=UINT32_MAX,greatest=0;
  for(unsigned i=0;i<16;++i){
   const uint32_t mv=analogReadMilliVolts(BATTERY_ADC_GPIO);
   sum+=mv;least=min(least,mv);greatest=max(greatest,mv);
   vTaskDelay(pdMS_TO_TICKS(2));
  }
  // Trim one sample at each end; store one coherent telemetry snapshot.
  const uint32_t pinMv=(sum-least-greatest+7)/14;
  const uint32_t loadedMv=(pinMv*(BATTERY_DIVIDER_TOP_OHMS+BATTERY_DIVIDER_BOTTOM_OHMS)+BATTERY_DIVIDER_BOTTOM_OHMS/2)/BATTERY_DIVIDER_BOTTOM_OHMS;
  if(loadedMv<2700||loadedMv>4400){low=false;batteryState.store(0);}
  else{
   if(loadedMv<=BATTERY_LOW_ON_MV)low=true;
   else if(loadedMv>=BATTERY_LOW_OFF_MV)low=false;
   batteryState.store(BATTERY_STATE_VALID|(low?BATTERY_STATE_LOW:0)|loadedMv);
  }
  vTaskDelayUntil(&wake,pdMS_TO_TICKS(1000));
 }
}
void startBatteryMonitor(){
 // Separate low-priority task; ADC reads never run inside capture() or the ISR.
 if(xTaskCreatePinnedToCore(batteryTask,"battery",4096,nullptr,1,nullptr,0)!=pdPASS)
  batteryState.store(0);
}

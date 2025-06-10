#include <SPI.h>
#include "esp_timer.h"

// 定义宏，简化寄存器配置
#define CONFIG_1 0xD5
#define CONFIG_2 0xC0
#define CONFIG_3 0xEC
#define CHnSET 0x60
#define ENABLE_SRB1 0x20
#define BIAS_SENSP 0xFF
#define BIAS_SENSN 0xFF
#define LEAD_OFF_CURRENT 0x00
#define ENABLE_POSITIVE_LEAD_OFF 0x00
#define ENABLE_NEGATIVE_LEAD_OFF 0x00

// 定义模式常量
#define MODE_CONTINUOUS_READ 1
#define MODE_IMPEDANCE_MEASURE 2
#define MODE_SELF_TEST 3

int currentMode = MODE_CONTINUOUS_READ;  // 当前模式
volatile bool dataReady = false;  // 标志位
double channelDataBuffer[9];      // 缓冲区，用于保存读取的数据

// 函数声明
void IRAM_ATTR onDRDYInterrupt();  // DRDY引脚中断服务函数

void setup();
void loop();
void startContinuousReadMode();
void startImpedanceMeasurementMode();
void startSelfTestMode(); 
void initADS1299();
void measureImpedance();
void getDeviceID();
void sendCommand(byte cmd);
void writeRegister(byte reg, byte value);
byte readRegister(byte reg);
void readData();
void convertData(byte *data, double *channelData);

// 定义引脚
#define CS_PIN    A3
#define SCLK_PIN  SCK
#define MOSI_PIN  MOSI
#define MISO_PIN  MISO
#define DRDY_PIN  A0
#define START_PIN A2
#define RESET_PIN A1
// 定义命令
#define WAKEUP  0x02
#define STANDBY  0x04
#define RESET   0x06
#define START   0x08
#define STOP    0x0A
#define RDATAC  0x10
#define SDATAC  0x11
#define RDATA   0x12
#define RREG    0x20
#define WREG    0x40

void setup() {
  // 初始化串口
  Serial.begin(115200);

  // 初始化引脚
  pinMode(CS_PIN, OUTPUT);
  pinMode(SCLK_PIN, OUTPUT);
  pinMode(MOSI_PIN, OUTPUT);
  pinMode(MISO_PIN, INPUT);
  pinMode(DRDY_PIN, INPUT);
  pinMode(START_PIN, OUTPUT);
  pinMode(RESET_PIN, OUTPUT);

  digitalWrite(CS_PIN, LOW);
  digitalWrite(START_PIN, LOW);
  digitalWrite(RESET_PIN, HIGH);
  delay(100);

  // 初始化SPI
  SPI.begin(SCLK_PIN, MISO_PIN, MOSI_PIN, CS_PIN);
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE1);
  SPI.setClockDivider(SPI_CLOCK_DIV8);  // 约 5 MHz

  // 初始化ADS1299
  initADS1299();
  getDeviceID();
  Serial.println("ADS1299 initialized");

  // 配置外部中断（DRDY_PIN为低时触发中断）
  attachInterrupt(digitalPinToInterrupt(DRDY_PIN), onDRDYInterrupt, FALLING);
  currentMode = MODE_CONTINUOUS_READ;
}

void loop() {
  // 处理串口输入，切换ADS1299功能
  if (Serial.available()) {
    char cmd = Serial.read();
    Serial.print("收到:");
    Serial.println(cmd);
    if (cmd == '1') {
      currentMode = MODE_CONTINUOUS_READ;
      startContinuousReadMode();
    } else if (cmd == '2') {
      currentMode = MODE_IMPEDANCE_MEASURE;
      startImpedanceMeasurementMode();
    } else if (cmd == '3') {
      currentMode = MODE_SELF_TEST;
      startSelfTestMode();
    }

    
  }
  // 检查是否有数据准备好
  if (dataReady) {
    // 清除标志位
    dataReady = false;

    // 打印数据
    Serial.print("Channel:");
    for (int i = 0; i < 9; i++) {
      Serial.print(channelDataBuffer[i], 6);
      if (i != 8) {
        Serial.print(",");
      } else {
        Serial.println("");
      }
    }
  }
}

// DRDY引脚的中断服务函数
void IRAM_ATTR onDRDYInterrupt() {
  if (currentMode == MODE_CONTINUOUS_READ) {
    readData();  // 读取数据
  } else if (currentMode == MODE_IMPEDANCE_MEASURE) {
    measureImpedance();  // 测量阻抗
  } else if (currentMode == MODE_SELF_TEST) {
    readData();  // 读取数据
  }
}

void startContinuousReadMode() {
  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC);
  // 使用宏配置寄存器
  writeRegister(0x01, CONFIG_1);
  writeRegister(0x02, CONFIG_2);
  writeRegister(0x03, CONFIG_3);
  writeRegister(0x04, 0x00);
  for (int i = 0x05; i <= 0x0C; i++) {
    writeRegister(i, CHnSET);
  }
  writeRegister(0x0D, BIAS_SENSP);
  writeRegister(0x0E, BIAS_SENSN);
  writeRegister(0x15, ENABLE_SRB1); // 启用SRB1

  // 启动数据连续读取
  sendCommand(START);
  sendCommand(RDATAC);
}

void startImpedanceMeasurementMode() {
  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC);
  writeRegister(0x0F, LEAD_OFF_CURRENT); // 设置导联电流
  writeRegister(0x18, ENABLE_POSITIVE_LEAD_OFF); // 启用正极导联检测
  writeRegister(0x19, ENABLE_NEGATIVE_LEAD_OFF); // 启用负极导联检测
}

void startSelfTestMode() {
  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC);
  // 配置CONFIG2寄存器启用测试信号 1af 2hz
  writeRegister(0x01, 0xD5);
  writeRegister(0x02, 0xD1);
  writeRegister(0x03, 0xEC);
  writeRegister(0x04, 0x00); // MISC1寄存器启用SRB1
  // 配置所有通道输入为内部测试信号
  for (int i = 0x05; i <= 0x0C; i++) {
    writeRegister(i, 0x65); // 设置每个通道为测试信号
  }
  // 启动数据连续读取
  sendCommand(START);
  sendCommand(RDATAC);
}

void initADS1299() {
  sendCommand(RESET);
  delay(100);
  sendCommand(65);
  // 使用宏定义配置寄存器
  writeRegister(0x01, CONFIG_1); 
  writeRegister(0x02, CONFIG_2);
  writeRegister(0x03, CONFIG_3);
  writeRegister(0x04, 0x00); // MISC1寄存器
  
  for (int i = 0x05; i <= 0x0C; i++) {
    writeRegister(i, CHnSET); // 设置PGA增益和输入类型
  }
  writeRegister(0x0D, BIAS_SENSP);
  writeRegister(0x0E, BIAS_SENSN);
  writeRegister(0x15, ENABLE_SRB1); // 启用SRB1
  sendCommand(START);
  sendCommand(RDATAC); // 启动数据连续读取模式
}

void readData() {
  byte data[27];
  digitalWrite(CS_PIN, LOW);
  delayMicroseconds(1);  // 确保 tSDSU
  for (int i = 0; i < 27; i++) {
    data[i] = SPI.transfer(0x00);
  }
  digitalWrite(CS_PIN, HIGH);
  delayMicroseconds(1);  // 确保 tDSHD
  // 转换数据，并将结果保存在全局缓冲区
  convertData(data, channelDataBuffer);
  
  // 设置标志，表示数据已经准备好
  dataReady = true;
}

void measureImpedance() {
  byte data[27];
  digitalWrite(CS_PIN, LOW);
  for (int i = 0; i < 27; i++) {
    data[i] = SPI.transfer(0x00);
  }
  digitalWrite(CS_PIN, HIGH);

  double channelData[9];
  convertData(data, channelData);
  Serial.print("Channel:");
  for (int i = 0; i < 9; i++) {
    Serial.print(channelData[i], 6);
    if (i != 8) {
      Serial.print(",");
    } else {
      Serial.println("");
    }
  }
  Serial.print("Impedance Measurement:");
  for (int i = 0; i < 8; i++) {
    double voltage = channelData[i];
    double current = 0.000006; // 假设使用6nA的导联电流
    double impedance = voltage / current;
    Serial.print(impedance, 2); // 打印阻抗值
    if (i != 7) {
      Serial.print(",");
    } else {
      Serial.println("");
    }
  }
}

void convertData(byte *data, double *channelData) {
  // 解析STATUS寄存器
  long statusValue = ((long)data[0] << 16) | ((long)data[1] << 8) | data[2];
  channelData[0] = (double)statusValue;

  // 转换通道数据
  for (int i = 0; i < 8; i++) {
    long value = ((long)data[3*i+3] << 16) | ((long)data[3*i+4] << 8) | data[3*i+5];
    
    // 24位符号扩展
    if (value & 0x800000) {
      value |= 0xFF000000;  // 负数扩展
    }
    
    // 电压计算 (考虑增益)
    double vPerLSB = 4.5 / (24 * 8388608.0);  // 1 LSB对应电压
    channelData[i+1] = (double)value * vPerLSB;
  }
}

void sendCommand(byte cmd) {
  digitalWrite(CS_PIN, LOW);
  delayMicroseconds(1);  // 确保 tSDSU
  SPI.transfer(cmd);
  digitalWrite(CS_PIN, HIGH);
  delayMicroseconds(1);  // 确保 tSDSU
}

void writeRegister(byte reg, byte value) {
  digitalWrite(CS_PIN, LOW);
  delayMicroseconds(1);  // 确保 tSDSU
  SPI.transfer(WREG | reg);
  SPI.transfer(0x00);
  SPI.transfer(value);
  digitalWrite(CS_PIN, HIGH);
  delayMicroseconds(1);  // 确保 tSDSU
}

byte readRegister(byte reg) {
  digitalWrite(CS_PIN, LOW);
  delayMicroseconds(1);  // 确保 tSDSU
  SPI.transfer(RREG | reg);
  SPI.transfer(0x00);
  byte value = SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);
  delayMicroseconds(1);  // 确保 tSDSU
  return value;
}

void getDeviceID() {
  digitalWrite(CS_PIN, LOW);
  delayMicroseconds(1);  // 确保 tSDSU
  SPI.transfer(SDATAC);
  SPI.transfer(RREG | 0x00);
  SPI.transfer(0x00);
  byte data = SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);
  delayMicroseconds(1);  // 确保 tSDSU
  Serial.print("Device ID: ");
  Serial.println(data, BIN);
}
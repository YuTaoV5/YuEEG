#include <SPI.h>
#include "esp_timer.h"


// 函数声明
void IRAM_ATTR onDataTimer(void* arg);
void IRAM_ATTR onImpedanceTimer(void* arg);
void setup();
void drawSprite();
void readButtons();
void loop();
void startContinuousReadMode();
void startImpedanceMeasurementMode();
void initADS1299();
void measureImpedance();
void getDeviceID();
void sendCommand(byte cmd);
void writeRegister(byte reg, byte value);
byte readRegister(byte reg);
void readData();
void convertData(byte *data, double *channelData);

// 定义引脚
#define CS_PIN    15
#define SCLK_PIN  14
#define MOSI_PIN  13
#define MISO_PIN  12
#define DRDY_PIN  10
#define CLKSEL_PIN 11
#define START_PIN 1
#define RESET_PIN 2
#define PWDN_PIN  3

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

volatile boolean startRead = false;
volatile boolean startImpedanceRead = false;
volatile boolean readImpedance = false;
volatile boolean continuousReadMode = true;

esp_timer_handle_t dataTimer;
esp_timer_handle_t impedanceTimer;

// TFT_eSPI tft = TFT_eSPI();
// TFT_eSprite sprite = TFT_eSprite(&tft);

// float batteryVoltage;

// // 颜色定义
// #define gray 0x2A0A
// #define lines 0x8C71
// unsigned short rings[4] = { 0x47DD, 0xFB9F, 0x86BF, 0xFFD0 };

// // 图表变量
// int n = 0;
// int fromTop = 30;
// int fromLeft = 20;
// int w = 480;
// int h = 200;
// double channelData[9][20] = { 0 };

// 定义ESP32定时器回调函数
void IRAM_ATTR onDataTimer(void* arg) {
  if (digitalRead(DRDY_PIN) == LOW) {
    startRead = true;
  }
}

void IRAM_ATTR onImpedanceTimer(void* arg) {
  if (digitalRead(DRDY_PIN) == LOW) {
    startImpedanceRead = true;
  }
}

void setup() {
  // 初始化串口
  Serial.begin(115200);

  // 初始化引脚
  pinMode(CS_PIN, OUTPUT);
  pinMode(SCLK_PIN, OUTPUT);
  pinMode(MOSI_PIN, OUTPUT);
  pinMode(MISO_PIN, INPUT);
  pinMode(DRDY_PIN, INPUT);
  pinMode(CLKSEL_PIN, OUTPUT);
  pinMode(START_PIN, OUTPUT);
  pinMode(RESET_PIN, OUTPUT);
  pinMode(PWDN_PIN, OUTPUT);

  // 初始化SPI
  SPI.begin(SCLK_PIN, MISO_PIN, MOSI_PIN, CS_PIN);
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE1);
  SPI.setClockDivider(SPI_CLOCK_DIV4);

  // 初始化ADS1299
  initADS1299();
  getDeviceID();
  Serial.println("ADS1299 initialized");

  // 配置ESP32定时器
  const esp_timer_create_args_t dataTimer_args = {
      .callback = &onDataTimer,
      .name = "ADS1299 Data Timer"
  };

  const esp_timer_create_args_t impedanceTimer_args = {
      .callback = &onImpedanceTimer,
      .name = "ADS1299 Impedance Timer"
  };

  esp_timer_create(&dataTimer_args, &dataTimer);
  esp_timer_create(&impedanceTimer_args, &impedanceTimer);
}


void loop() {
  // 处理串口输入，切换ADS1299功能
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == '1') {
      startContinuousReadMode();
    } else if (cmd == '2') {
      startImpedanceMeasurementMode();
    }
  }

  if (startRead) {
    startRead = false;
    readData();
  }

  if (startImpedanceRead) {
    startImpedanceRead = false;
    measureImpedance();
  }

}

void startContinuousReadMode() {
  continuousReadMode = true;
  readImpedance = false;
  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC);
  writeRegister(0x01, 0x96); // 设置数据速率为1kSPS
  writeRegister(0x02, 0xD0); // 内部参考电压和偏置电流
  writeRegister(0x03, 0xE0); // 启用偏置驱动器
  writeRegister(0x04, 0x20); // 设置MISC1寄存器，启用SRB1
  for (int i = 0x05; i <= 0x0C; i++) {
    writeRegister(i, 0x60); // 设置PGA增益和输入类型
  }
  writeRegister(0x0D, 0xFF); // BIAS_SENSP
  writeRegister(0x0E, 0xFF); // BIAS_SENSN
  sendCommand(START);
  sendCommand(RDATAC); // 启动数据连续读取模式
  esp_timer_start_periodic(dataTimer, 1000); // 1ms间隔
  esp_timer_stop(impedanceTimer);
}

void startImpedanceMeasurementMode() {
  continuousReadMode = false;
  readImpedance = true;
  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC);
  // 配置导联电流进行阻抗测量
  writeRegister(0x0F, 0x02); // 设置LOFF寄存器，导联电流为6nA或其他适当值
  writeRegister(0x18, 0xFF); // 启用所有正极通道的导联检测
  writeRegister(0x19, 0xFF); // 启用所有负极通道的导联检测
  esp_timer_start_periodic(impedanceTimer, 1000); // 1ms间隔
  esp_timer_stop(dataTimer);
}

void initADS1299() {
  digitalWrite(CLKSEL_PIN, HIGH);
  digitalWrite(CS_PIN, LOW);
  digitalWrite(START_PIN, LOW);
  digitalWrite(RESET_PIN, HIGH);
  digitalWrite(PWDN_PIN, HIGH);
  delay(100);

  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC);
  writeRegister(0x01, 0x96); // 设置数据速率为1kSPS
  writeRegister(0x02, 0xD0); // 内部参考电压和偏置电流
  writeRegister(0x03, 0xE0); // 启用偏置驱动器
  writeRegister(0x04, 0x20); // 设置MISC1寄存器，启用SRB1
  for (int i = 0x05; i <= 0x0C; i++) {
    writeRegister(i, 0x60); // 设置PGA增益和输入类型
  }
  writeRegister(0x0D, 0xFF); // BIAS_SENSP
  writeRegister(0x0E, 0xFF); // BIAS_SENSN
  sendCommand(START);
  sendCommand(RDATAC); // 启动数据连续读取模式
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

void getDeviceID() {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(SDATAC);
  SPI.transfer(RREG | 0x00);
  SPI.transfer(0x00);
  byte data = SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);
  Serial.print("Device ID: ");
  Serial.println(data, BIN);
}

void sendCommand(byte cmd) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(cmd);
  digitalWrite(CS_PIN, HIGH);
}

void writeRegister(byte reg, byte value) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(WREG | reg);
  SPI.transfer(0x00);
  SPI.transfer(value);
  digitalWrite(CS_PIN, HIGH);
}

byte readRegister(byte reg) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(RREG | reg);
  SPI.transfer(0x00);
  byte value = SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);
  return value;
}

void readData() {
  digitalWrite(CS_PIN, LOW);
  byte data[27];
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
}

void convertData(byte *data, double *channelData) {
  for (int i = 0; i < 9; i++) {
    long value = ((long)data[3 * i + 3] << 16) | ((long)data[3 * i + 4] << 8) | data[3 * i + 5];
    if (value & 0x800000) {
      value |= 0xFF000000;
    }
    channelData[i] = (double)value * 4.5 / (double)0x7FFFFF;
  }
}
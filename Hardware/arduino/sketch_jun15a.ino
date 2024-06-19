#include <SPI.h>
#include "esp_timer.h"

// 定义引脚
#define CS_PIN    10
#define SCLK_PIN  12
#define MOSI_PIN  11
#define MISO_PIN  13
#define DRDY_PIN  15
#define CLKSEL_PIN 16
#define START_PIN 18
#define RESET_PIN 8
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
volatile boolean readLeadOff = false;
volatile boolean continuousReadMode = true;

esp_timer_handle_t dataTimer;
esp_timer_handle_t impedanceTimer;

void IRAM_ATTR onDataTimer(void* arg) {
  if (digitalRead(DRDY_PIN) == LOW) {
    startRead = true;
  }
}

void IRAM_ATTR onImpedanceTimer(void* arg) {
  readLeadOffStatus();
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
  Serial.println("ADS1299 初始化完成");

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
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == '1') {
      startContinuousReadMode();
    } else if (cmd == '2') {
      startLeadOffDetectionMode();
    }
  }

  if (startRead) {
    startRead = false;
    readData();
  }
}

void startContinuousReadMode() {
  continuousReadMode = true;
  readLeadOff = false;
  // 复位芯片
  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC); // 停止数据连续读取
  // 配置寄存器
  writeRegister(0x01, 0x96); // CONFIG1 设置数据速率为1kSPS
  writeRegister(0x02, 0xD0); // CONFIG2 内部参考电压和偏置电流
  writeRegister(0x03, 0xE0); // CONFIG3 启用偏置驱动器
  for (int i = 0x05; i <= 0x0C; i++) {
    writeRegister(i, 0x60); // CHxSET 设置PGA增益和输入类型
  }
  writeRegister(0x0D, 0xFF); // BIAS_SENSP
  writeRegister(0x0E, 0xFF); // BIAS_SENSN
  // 启动连续数据读取模式
  sendCommand(START);
  sendCommand(RDATAC); // 启动数据连续读取模式
  esp_timer_start_periodic(dataTimer, 1000); // 1000微秒 = 1毫秒
  esp_timer_stop(impedanceTimer); // 停止阻抗读取定时器
}

void startLeadOffDetectionMode() {
  continuousReadMode = false;
  readLeadOff = true;
  // 复位芯片
  sendCommand(RESET);
  delay(100);
  sendCommand(SDATAC); // 停止数据连续读取
  // 配置导联脱落检测
  writeRegister(0x0F, 0x02); // LOFF寄存器，设置为6nA
  writeRegister(0x18, 0xFF); // 启用所有通道的正极导联检测
  writeRegister(0x19, 0xFF); // 启用所有通道的负极导联检测
  esp_timer_start_periodic(impedanceTimer, 100000); // 100000微秒 = 100毫秒
  esp_timer_stop(dataTimer); // 停止数据读取定时器
}

void initADS1299() {
  // 启动时序
  digitalWrite(CLKSEL_PIN, HIGH);
  digitalWrite(CS_PIN, LOW);
  digitalWrite(START_PIN, LOW);
  digitalWrite(RESET_PIN, HIGH);
  digitalWrite(PWDN_PIN, HIGH);
  delay(100);

  // 复位芯片
  sendCommand(RESET);
  delay(100);

  // 停止连续读取模式
  sendCommand(SDATAC);

  // 配置寄存器
  writeRegister(0x01, 0x96); // CONFIG1 设置数据速率为1kSPS
  writeRegister(0x02, 0xD0); // CONFIG2 内部参考电压和偏置电流
  writeRegister(0x03, 0xE0); // CONFIG3 启用偏置驱动器
  for (int i = 0x05; i <= 0x0C; i++) {
    writeRegister(i, 0x60); // CHxSET 设置PGA增益和输入类型
  }
  writeRegister(0x0D, 0xFF); // BIAS_SENSP
  writeRegister(0x0E, 0xFF); // BIAS_SENSN
  // 启动连续数据读取模式
  sendCommand(START);
  sendCommand(RDATAC);
}

void readLeadOffStatus() {
  byte statP = readRegister(0x1C); // 读取LOFF_STATP寄存器
  byte statN = readRegister(0x1D); // 读取LOFF_STATN寄存器

  Serial.print("Lead-Off Status:");

  for (int i = 0; i < 8; i++) {
    bool pStatus = statP & (1 << i);
    bool nStatus = statN & (1 << i);
    Serial.print(pStatus ? "Off" : "On");
    if (i != 7) {
      Serial.print(",");
    } else {
      Serial.println("");
    }
  }
  // 读取导联检测结果
  // readLeadOffImpedance();
}

void readLeadOffImpedance() {
  byte data[27];
  digitalWrite(CS_PIN, LOW);
  for (int i = 0; i < 27; i++) {
    data[i] = SPI.transfer(0x00);
  }
  digitalWrite(CS_PIN, HIGH);

  // 转换数据
  double channelData[9];
  convertData(data, channelData);

  // 输出导联阻抗
  Serial.print("Lead-Off Impedance:");
  for (int i = 0; i < 8; i++) {
    Serial.print(channelData[i], 6);
    if (i != 7) {
      Serial.print(",");
    } else {
      Serial.println("");
    }
  }
}

void getDeviceID() {
  digitalWrite(CS_PIN, LOW); // 低电平以进行通信
  SPI.transfer(SDATAC);      // 停止连续读取数据模式
  SPI.transfer(RREG | 0x00); // 读取寄存器命令
  SPI.transfer(0x00);        // 请求一个字节
  byte data = SPI.transfer(0x00); // 读取字节
  digitalWrite(CS_PIN, HIGH); // 高电平以结束通信
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
  SPI.transfer(0x00); // 写一个寄存器
  SPI.transfer(value);
  digitalWrite(CS_PIN, HIGH);
}

byte readRegister(byte reg) {
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(RREG | reg);
  SPI.transfer(0x00); // 读取一个寄存器
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

  // 转换为9通道的double数据
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
    if (value & 0x800000) { // 如果最高位为1，则为负数
      value |= 0xFF000000; // 扩展符号位
    }
    channelData[i] = (double)value * 4.5 / (double)0x7FFFFF; // 将值转换为电压
  }
}

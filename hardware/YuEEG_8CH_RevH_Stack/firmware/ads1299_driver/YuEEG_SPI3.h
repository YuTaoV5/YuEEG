// IMU transport candidate: common SPI3 host, ADS1299 remains on SPI2.
#pragma once
#include <driver/spi_master.h>
constexpr int SPI3_PANEL_CS=2,SPI3_IMU_CS=43,IMU_DRDY_GPIO=44;
constexpr int SPI3_CLK_GPIO=8,SPI3_MOSI_GPIO=9,SPI3_MISO_GPIO=14,SPI3_D2_GPIO=15,SPI3_D3_GPIO=16;
constexpr size_t SHARED_SPI3_PIXEL_ROWS=4;
constexpr size_t SHARED_SPI3_MAX_BYTES=368*SHARED_SPI3_PIXEL_ROWS*2;
static bool sharedSpi3Ready=false;
bool beginSharedSpi3(){
 if(sharedSpi3Ready)return true;
 for(int gpio:{SPI3_PANEL_CS,SPI3_IMU_CS}){digitalWrite(gpio,HIGH);pinMode(gpio,OUTPUT);}
 for(int gpio:{SPI3_CLK_GPIO,SPI3_MOSI_GPIO,SPI3_MISO_GPIO,SPI3_D2_GPIO,SPI3_D3_GPIO}){digitalWrite(gpio,LOW);pinMode(gpio,OUTPUT);}
 spi_bus_config_t bus{};bus.sclk_io_num=SPI3_CLK_GPIO;bus.mosi_io_num=SPI3_MOSI_GPIO;bus.miso_io_num=SPI3_MISO_GPIO;
 bus.quadwp_io_num=SPI3_D2_GPIO;bus.quadhd_io_num=SPI3_D3_GPIO;bus.max_transfer_sz=SHARED_SPI3_MAX_BYTES;
 bus.flags=SPICOMMON_BUSFLAG_MASTER|SPICOMMON_BUSFLAG_QUAD;
 sharedSpi3Ready=spi_bus_initialize(SPI3_HOST,&bus,SPI_DMA_CH_AUTO)==ESP_OK;
 return sharedSpi3Ready;
}
bool attachSharedSpi3(const spi_device_interface_config_t& config,spi_device_handle_t* handle){
 return sharedSpi3Ready&&spi_bus_add_device(SPI3_HOST,&config,handle)==ESP_OK;
}
// Once attached, each task owns its device handle. IDF arbitrates transactions.
// The host stays initialized if either device fails; one task must not free it.

# Display attribution

CO5300 register settings and the 16-pixel x offset in YuEEG_UI.h were adapted from OSPTEK 鱼鹰光电's AM178Q368448LK ESP32-S3 QSPI bring-up example, supplied by the user in `hardware/display-amoled-1.78inch-368x448-main`. Original paths: `examples/esp32s3-co5300-qspi-bringup/main/app_init/lcd_init.c` and `components/esp_lcd_qspi_amoled/esp_lcd_qspi_amoled.c` under that example. OSPTEK-authored materials are CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ . The component driver carries its own Apache-2.0 notice; YuEEG does not redistribute that component or copy its implementation.

YuEEG adaptations: Arduino/ESP-IDF SPI transport, 368x448 bounded write windows, TE disabled, lower brightness, status-only rendering, power-error handling. No endorsement by OSPTEK is implied. Original OSPTEK license and init source are archived with the Rev G hardware references. Third-party IC/connector datasheets retain their owners' rights.

/*
 * SPDX-FileCopyrightText: Copyright 2026 OSPTEK
 * SPDX-License-Identifier: CC-BY-4.0
 *
 * https://github.com/osptek
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_err.h"

#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_co5300.h"
#include "esp_lcd_touch.h"
#include "esp_lcd_touch_cst820.h"

#include "driver/spi_master.h"
#include "driver/i2c_master.h"

#include "esp_lv_adapter.h"
#include "lvgl.h"
#include "lv_demos.h"

#include "co5300_init_cmds.h"

static const char *TAG = "LVGL_CO5300_CST820_QSPI";

// ==================== 引脚定义（请根据你的硬件修改） ====================
#define EXAMPLE_PIN_NUM_LCD_CS      GPIO_NUM_9
#define EXAMPLE_PIN_NUM_LCD_SCK     GPIO_NUM_12
#define EXAMPLE_PIN_NUM_LCD_D0      GPIO_NUM_13   // QSPI D0
#define EXAMPLE_PIN_NUM_LCD_D1      GPIO_NUM_14   // QSPI D1
#define EXAMPLE_PIN_NUM_LCD_D2      GPIO_NUM_15   // QSPI D2
#define EXAMPLE_PIN_NUM_LCD_D3      GPIO_NUM_16   // QSPI D3
#define EXAMPLE_PIN_NUM_LCD_RST     GPIO_NUM_10
#define EXAMPLE_PIN_NUM_LCD_TE      GPIO_NUM_11   //未使用

#define EXAMPLE_TOUCH_I2C_SCL       GPIO_NUM_40
#define EXAMPLE_TOUCH_I2C_SDA       GPIO_NUM_39
#define EXAMPLE_TOUCH_RST           GPIO_NUM_41
#define EXAMPLE_TOUCH_INT           GPIO_NUM_42

/* Touch settings */
#define EXAMPLE_TOUCH_I2C_NUM       I2C_NUM_0
#define EXAMPLE_TOUCH_I2C_CLK_HZ    (400 * 1000)

// ==================== 显示参数 ====================
#define EXAMPLE_LCD_HOST            SPI2_HOST
#define EXAMPLE_LCD_PIXEL_CLOCK_HZ  (40 * 1000 * 1000)

#define EXAMPLE_LCD_H_RES           460
#define EXAMPLE_LCD_V_RES           460    
#define EXAMPLE_LCD_X_GAP           10
#define EXAMPLE_LCD_Y_GAP           0

// ==================== CO5300 区域对齐回调 ====================
static void co5300_area_rounder_cb(lv_area_t *area, void *user_data)
{
    uint16_t x1 = area->x1;
    uint16_t x2 = area->x2;
    uint16_t y1 = area->y1;
    uint16_t y2 = area->y2;

    // round the start of coordinate down to the nearest 2M number
    area->x1 = (x1 >> 1) << 1;
    area->y1 = (y1 >> 1) << 1;
    // round the end of coordinate up to the nearest 2N+1 number
    area->x2 = ((x2 >> 1) << 1) + 1;
    area->y2 = ((y2 >> 1) << 1) + 1;
}

void app_main(void)
{
    ESP_LOGI(TAG, "ESP32-S3 + CO5300 (QSPI) + CST820 + LVGL9 开始初始化...");

    // 1. QSPI 总线初始化
    spi_bus_config_t bus_config = CO5300_PANEL_BUS_QSPI_CONFIG(
        EXAMPLE_PIN_NUM_LCD_SCK,
        EXAMPLE_PIN_NUM_LCD_D0,
        EXAMPLE_PIN_NUM_LCD_D1,
        EXAMPLE_PIN_NUM_LCD_D2,
        EXAMPLE_PIN_NUM_LCD_D3,
        EXAMPLE_LCD_H_RES * 80 * sizeof(uint16_t)
    );
    ESP_ERROR_CHECK(spi_bus_initialize(EXAMPLE_LCD_HOST, &bus_config, SPI_DMA_CH_AUTO));

    // 2. LCD Panel IO (QSPI)
    esp_lcd_panel_io_spi_config_t io_config = {
        .cs_gpio_num = EXAMPLE_PIN_NUM_LCD_CS,
        .dc_gpio_num = -1,
        .spi_mode = 0,
        .pclk_hz = EXAMPLE_LCD_PIXEL_CLOCK_HZ,
        .trans_queue_depth = 1,
        .lcd_cmd_bits = 32,
        .lcd_param_bits = 8,
        .flags = {
            .quad_mode = true,
        },
    };
    esp_lcd_panel_io_handle_t panel_io = NULL;
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)EXAMPLE_LCD_HOST, &io_config, &panel_io));

    // 3. CO5300 Panel 初始化
    co5300_vendor_config_t vendor_config = {
        .init_cmds = lcd_init_cmds,
        .init_cmds_size = lcd_init_cmds_size,
        .flags = {
            .use_qspi_interface = 1,
        },
    };
    esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = EXAMPLE_PIN_NUM_LCD_RST,
        .rgb_endian = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
        .vendor_config = &vendor_config,
    };

    esp_lcd_panel_handle_t panel_handle = NULL;
    ESP_ERROR_CHECK(esp_lcd_new_panel_co5300(panel_io, &panel_config, &panel_handle));

    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_set_gap(panel_handle, EXAMPLE_LCD_X_GAP, EXAMPLE_LCD_Y_GAP));
    // 在打开屏幕或背光之前，用户可以将预定义的图案刷新到屏幕上
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel_handle, true));
    ESP_ERROR_CHECK(esp_lcd_panel_co5300_set_brightness(panel_handle, 80));

    ESP_LOGI(TAG, "CO5300 QSPI 显示初始化完成 (%dx%d)", EXAMPLE_LCD_H_RES, EXAMPLE_LCD_V_RES);

    // 4. CST820 触摸初始化（I2C）
    i2c_master_bus_config_t i2c_bus_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = EXAMPLE_TOUCH_I2C_NUM,
        .scl_io_num = EXAMPLE_TOUCH_I2C_SCL,
        .sda_io_num = EXAMPLE_TOUCH_I2C_SDA,
        .flags.enable_internal_pullup = true,
    };
    i2c_master_bus_handle_t i2c_bus;
    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_bus_config, &i2c_bus));

    esp_lcd_panel_io_i2c_config_t tp_io_config = ESP_LCD_TOUCH_IO_I2C_CST820_CONFIG();
    tp_io_config.scl_speed_hz = EXAMPLE_TOUCH_I2C_CLK_HZ;

    esp_lcd_panel_io_handle_t tp_io_handle = NULL;
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_i2c(i2c_bus, &tp_io_config, &tp_io_handle));

    esp_lcd_touch_config_t tp_cfg = {
        .x_max = EXAMPLE_LCD_H_RES,
        .y_max = EXAMPLE_LCD_V_RES,
        .rst_gpio_num = EXAMPLE_TOUCH_RST,
        .int_gpio_num = EXAMPLE_TOUCH_INT,
        .levels = {.reset = 0, .interrupt = 0},
        .flags = {
            .swap_xy = 0,
            .mirror_x = 0,
            .mirror_y = 0,
        },
    };
    esp_lcd_touch_handle_t touch_handle = NULL;
    ESP_ERROR_CHECK(esp_lcd_touch_new_i2c_cst820(tp_io_handle, &tp_cfg, &touch_handle));

    ESP_LOGI(TAG, "CST820 触控初始化完成");

    // 5. esp_lvgl_adapter 初始化
    esp_lv_adapter_config_t adapter_cfg = ESP_LV_ADAPTER_DEFAULT_CONFIG();
    adapter_cfg.stack_in_psram = true; // 尝试将任务栈放入PSRAM
    ESP_ERROR_CHECK(esp_lv_adapter_init(&adapter_cfg));

    // 注册显示器（QSPI 使用 SPI 宏）
    esp_lv_adapter_display_config_t disp_cfg =
        ESP_LV_ADAPTER_DISPLAY_SPI_WITH_PSRAM_DEFAULT_CONFIG(
            panel_handle,
            panel_io,
            EXAMPLE_LCD_H_RES,
            EXAMPLE_LCD_V_RES,
            ESP_LV_ADAPTER_ROTATE_0);   // 根据实际画面方向修改（0/90/180/270）

    lv_display_t *disp = esp_lv_adapter_register_display(&disp_cfg);
    assert(disp != NULL);

    // 设置背景颜色为黑色
    lv_obj_t *default_scr = lv_disp_get_scr_act(disp);     // 获取当前活动屏幕
    if (default_scr) {
        lv_obj_remove_style_all(default_scr);               // 清除默认样式
        lv_obj_set_style_bg_color(default_scr, lv_color_black(), LV_STATE_DEFAULT);
        lv_obj_set_style_bg_opa(default_scr, LV_OPA_COVER, LV_STATE_DEFAULT);
        lv_obj_set_size(default_scr, LV_PCT(100), LV_PCT(100));
    }

    //注册对齐回调
    ESP_ERROR_CHECK(esp_lv_adapter_set_area_rounder_cb(disp, co5300_area_rounder_cb, NULL));

    // 注册触摸输入设备
    esp_lv_adapter_touch_config_t touch_cfg = ESP_LV_ADAPTER_TOUCH_DEFAULT_CONFIG(disp, touch_handle);
    lv_indev_t *indev = esp_lv_adapter_register_touch(&touch_cfg);
    assert(indev != NULL);

    ESP_ERROR_CHECK(esp_lv_adapter_start());
    ESP_LOGI(TAG, "esp_lvgl_adapter 启动成功！");

    // 6. 创建 LVGL UI（必须在锁内操作）
    if (esp_lv_adapter_lock(portMAX_DELAY) == ESP_OK) {

        lv_demo_widgets();           // 官方 widget demo
        // lv_demo_music();             // 音乐 demo
        // lv_demo_benchmark();         // 性能测试

        esp_lv_adapter_unlock();
    }

    ESP_LOGI(TAG, "LVGL UI 创建完成，系统正常运行...");
}

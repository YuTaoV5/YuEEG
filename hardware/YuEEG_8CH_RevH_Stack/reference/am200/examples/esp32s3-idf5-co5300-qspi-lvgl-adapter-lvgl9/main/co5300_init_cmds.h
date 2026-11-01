#ifndef CO5300_INIT_CMDS_H
#define CO5300_INIT_CMDS_H

#include "esp_lcd_co5300.h"

#ifdef __cplusplus
extern "C" {
#endif

// ==================== CO5300 初始化命令数组 ====================
static const co5300_lcd_init_cmd_t lcd_init_cmds[] = {
    {0xFE, (uint8_t []){0x00}, 1, 0},
    {0x11, (uint8_t []){0x00}, 0, 120},
    // {0x35, (uint8_t []){0x00}, 1, 0},
    {0xFE, (uint8_t []){0x00}, 1, 0},
    {0xC4, (uint8_t []){0x80}, 1, 0},
    {0x3A, (uint8_t []){0x55}, 1, 0},
    {0x53, (uint8_t []){0x20}, 1, 0},
    {0x63, (uint8_t []){0xFF}, 1, 0},
    {0x2A, (uint8_t []){0x00, 0x00, 0x01, 0xBF}, 4, 0},
    {0x2B, (uint8_t []){0x00, 0x00, 0x01, 0x6F}, 4, 0},
    {0x29, (uint8_t []){0x00}, 0, 60},
    // {0x51, (uint8_t []){0xFF}, 1, 0},
    {0x51, (uint8_t []){0x00}, 1, 0},
    {0x58, (uint8_t []){0x07}, 1, 10},
};

static const size_t lcd_init_cmds_size = sizeof(lcd_init_cmds) / sizeof(co5300_lcd_init_cmd_t);

#ifdef __cplusplus
}
#endif

#endif // CO5300_INIT_CMDS_H
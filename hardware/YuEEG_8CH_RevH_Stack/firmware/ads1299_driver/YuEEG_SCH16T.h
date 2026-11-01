//****************************************************************************************
// @file    SCH16T.h
// @brief   Header file for the SCH1 library functions.
//
// @attention
//
// This software is released under the BSD license as follows.
// Copyright (c) 2024, Murata Electronics Oy.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following
// conditions are met:
//    1. Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//    2. Redistributions in binary form must reproduce the above
//       copyright notice, this list of conditions and the following
//       disclaimer in the documentation and/or other materials
//       provided with the distribution.
//    3. Neither the name of Murata Electronics Oy nor the names of its
//       contributors may be used to endorse or promote products derived
//       from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
// FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
// COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
// HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
// STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
// IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//****************************************************************************************


#ifndef SCH16T_H
#define SCH16T_H

#include <Arduino.h>
#include "YuEEG_SafeSpi.h"
#include <driver/spi_master.h>

/**
 * API return codes
 */
#define SCH16T_OK                      0
#define SCH16T_ERR_NULL_POINTER       -1
#define SCH16T_ERR_INVALID_PARAM      -2
#define SCH16T_ERR_SENSOR_INIT        -3
#define SCH16T_ERR_OTHER              -4


// SCH1 raw unprocessed data values
typedef struct {
    int32_t Rate1_raw[3];
    int32_t Rate2_raw[3];
    int32_t Acc1_raw[3];
    int32_t Acc2_raw[3];
    int32_t Acc3_raw[3];
    int32_t Temp_raw;
    bool frame_error;
    uint8_t Rate2_counter[3], Acc2_counter[3];
    bool generation_consistent;
} SCH16T_raw_data;


// SCH1 scaled measurement results
typedef struct {
    float Rate1[3];
    float Rate2[3];
    float Acc1[3];
    float Acc2[3];
    float Acc3[3];
    float Temp;
} SCH16T_result;


// SCH1 status data
typedef struct {
    uint16_t Summary;
    uint16_t Summary_Sat;
    uint16_t Common;
    uint16_t Rate_Common;
    uint16_t Rate_X;
    uint16_t Rate_Y;
    uint16_t Rate_Z;
    uint16_t Acc_X;
    uint16_t Acc_Y;
    uint16_t Acc_Z;
} SCH16T_status;


// SCH1 filters
typedef struct {
    uint16_t Rate12;
    uint16_t Acc12;
    uint16_t Acc3;
} SCH16T_filter;


// SCH1 sensitivities
typedef struct {
    uint16_t Rate1;
    uint16_t Rate2;
    uint16_t Acc1;
    uint16_t Acc2;
    uint16_t Acc3;
} SCH16T_sensitivity;


// SCH1 decimation
typedef struct {
    uint16_t Rate2;
    uint16_t Acc2;
} SCH16T_decimation;

// Measurement axes
typedef enum
{
    SCH16T_AXIS_X,
    SCH16T_AXIS_Y,
    SCH16T_AXIS_Z
} SCH16T_axis;

class SCH16T
{
    private:
        /**
         * SCH1 Standard requests
         */
        typedef enum {
            // Rate and acceleration
            REQ_READ_RATE_X1 = 0x0048000000AC,
            REQ_READ_RATE_Y1 = 0x00880000009A,
            REQ_READ_RATE_Z1 = 0x00C80000006D,
            REQ_READ_ACC_X1  = 0x0108000000F6,
            REQ_READ_ACC_Y1  = 0x014800000001,
            REQ_READ_ACC_Z1  = 0x018800000037,
            REQ_READ_ACC_X3  = 0x01C8000000C0,
            REQ_READ_ACC_Y3  = 0x02080000002E,
            REQ_READ_ACC_Z3  = 0x0248000000D9,
            REQ_READ_RATE_X2 = 0x0288000000EF,
            REQ_READ_RATE_Y2 = 0x02C800000018,
            REQ_READ_RATE_Z2 = 0x030800000083,
            REQ_READ_ACC_X2  = 0x034800000074,
            REQ_READ_ACC_Y2  = 0x038800000042,
            REQ_READ_ACC_Z2  = 0x03C8000000B5,

            // Status
            REQ_READ_STAT_SUM      = 0x05080000001C,
            REQ_READ_STAT_SUM_SAT  = 0x0548000000EB,
            REQ_READ_STAT_COM      = 0x0588000000DD,
            REQ_READ_STAT_RATE_COM = 0x05C80000002A,
            REQ_READ_STAT_RATE_X   = 0x0608000000C4,
            REQ_READ_STAT_RATE_Y   = 0x064800000033,
            REQ_READ_STAT_RATE_Z   = 0x068800000005,
            REQ_READ_STAT_ACC_X    = 0x06C8000000F2,
            REQ_READ_STAT_ACC_Y    = 0x070800000069,
            REQ_READ_STAT_ACC_Z    = 0x07480000009E,

            // Temperature and traceability
            REQ_READ_TEMP    = 0x0408000000B1,
            REQ_READ_SN_ID1  = 0x0F4800000065,
            REQ_READ_SN_ID2  = 0x0F8800000053,
            REQ_READ_SN_ID3  = 0x0FC8000000A4,
            REQ_READ_COMP_ID = 0x0F0800000092,

            // Filters
            REQ_READ_FILT_RATE  = 0x0948000000FA,
            REQ_READ_FILT_ACC12 = 0x0988000000CC,
            REQ_READ_FILT_ACC3  = 0x09C80000003B,
            REQ_READ_RATE_CTRL  = 0x0A08000000D5,
            REQ_READ_ACC12_CTRL = 0x0A4800000022,
            REQ_READ_ACC3_CTRL  = 0x0A8800000014,
            REQ_READ_MODE_CTRL  = 0x0D4800000010,
            REQ_SET_FILT_RATE   = 0x0968000000,    // For building Rate_XYZ1/2 filter setting frame.
            REQ_SET_FILT_ACC12  = 0x09A8000000,    // For building Acc_XYZ1/2 filter setting frame.
            REQ_SET_FILT_ACC3   = 0x09E8000000,    // For building Acc_XYZ3 filter setting frame.

            // Sensitivity and decimation
            REQ_SET_RATE_CTRL  = 0x0A28000000,   // For building Rate_XYZ1/2 sensitivity and
                                                //     Rate_XYZ2 decimation setting frame.
            REQ_SET_ACC12_CTRL = 0x0A68000000,   // For building Acc_XYZ1/2 sensitivity and
                                                //     Acc_XYZ2 decimation setting frame.
            REQ_SET_ACC3_CTRL  = 0x0AA8000000,   // For building Acc_XYZ3 sensitivity setting frame.
            REQ_SET_MODE_CTRL  = 0x0D68000000,   // For building MODE-register setting frame.

            // DRY/SYNC configuration
            REQ_READ_USER_IF_CTRL = 0x0CC80000007C,
            REQ_SET_USER_IF_CTRL  = 0x0CE8000000,    // For building USER_IF_CTRL -register setting frame.

            // Other
            REQ_SOFTRESET = 0x0DA800000AC3  // SPI soft reset command.
        } request;

        /**
         * Frame field masks
         */
        typedef enum {
            TA_FIELD_MASK    = 0xFFC000000000,
            SA_FIELD_MASK    = 0x7FE000000000,
            DATA_FIELD_MASK  = 0x00000FFFFF00,
            CRC_FIELD_MASK   = 0x0000000000FF,
            ERROR_FIELD_MASK = 0x001E00000000
        } frame_mask;

        typedef enum {
            /**
             * Status Summary Register bit definitions
             */
            S_SUM_CMN      = 0x0080,
            S_SUM_RATE_X   = 0x0040,
            S_SUM_RATE_Y   = 0x0020,
            S_SUM_RATE_Z   = 0x0010,
            S_SUM_ACC_X    = 0x0008,
            S_SUM_ACC_Y    = 0x0004,
            S_SUM_ACC_Z    = 0x0002,
            S_SUM_INIT_RDY = 0x0001,

            /**
             * Saturation Status Summary Register bit definitions
             */
            S_SUM_SAT_RATE_X1 = 0x4000,
            S_SUM_SAT_RATE_Y1 = 0x2000,
            S_SUM_SAT_RATE_Z1 = 0x1000,
            S_SUM_SAT_ACC_X1  = 0x0800,
            S_SUM_SAT_ACC_Y1  = 0x0400,
            S_SUM_SAT_ACC_Z1  = 0x0200,
            S_SUM_SAT_ACC_X3  = 0x0100,
            S_SUM_SAT_ACC_Y3  = 0x0080,
            S_SUM_SAT_ACC_Z3  = 0x0040,
            S_SUM_SAT_RATE_X2 = 0x0020,
            S_SUM_SAT_RATE_Y2 = 0x0010,
            S_SUM_SAT_RATE_Z2 = 0x0008,
            S_SUM_SAT_ACC_X2  = 0x0004,
            S_SUM_SAT_ACC_Y2  = 0x0002,
            S_SUM_SAT_ACC_Z2  = 0x0001,

            /**
             * Common Status Register bit definitions
             */
            S_COM_MCLK        = 0x0400,
            S_COM_DUAL_CLOCK  = 0x0200,
            S_COM_DSP         = 0x0100,
            S_COM_SVM         = 0x0080,
            S_COM_HV_CP       = 0x0040,
            S_COM_SUPPLY      = 0x0020,
            S_COM_TEMP        = 0x0010,
            S_COM_NMODE       = 0x0008,
            S_COM_NVM_STS     = 0x0004,
            S_COM_CMN_STS     = 0x0002,
            S_COM_CMN_STS_RDY = 0x0001,

            /**
             * Rate Common Status Register bit definitions
             */
            S_RATE_COM_PRI_AGC   = 0x0080,
            S_RATE_COM_PRI       = 0x0040,
            S_RATE_COM_PRI_START = 0x0020,
            S_RATE_COM_HV        = 0x0010,
            S_RATE_COM_SD_STS    = 0x0004,
            S_RATE_COM_BOND_STS  = 0x0002,
            S_RATE_COM_STS_RDY   = 0x0001,

            /**
             * Rate Status X Register bit definitions
             */
            S_RATE_X_DEC_SAT  = 0x0200,
            S_RATE_X_INTP_SAT = 0x0100,
            S_RATE_X_STC_DIG  = 0x0040,
            S_RATE_X_STC_ANA  = 0x0020,
            S_RATE_X_QC       = 0x0010,

            /**
             * Rate Status Y Register bit definitions
             */
            S_RATE_Y_DEC_SAT  = 0x0200,
            S_RATE_Y_INTP_SAT = 0x0100,
            S_RATE_Y_STC_DIG  = 0x0040,
            S_RATE_Y_STC_ANA  = 0x0020,
            S_RATE_Y_QC       = 0x0010,

            /**
             * Rate Status Z Register bit definitions
             */
            S_RATE_Z_DEC_SAT  = 0x0200,
            S_RATE_Z_INTP_SAT = 0x0100,
            S_RATE_Z_STC_DIG  = 0x0040,
            S_RATE_Z_STC_ANA  = 0x0020,
            S_RATE_Z_QC       = 0x0010,

            /**
             * ACC Status X Register bit definitions
             */
            S_ACC_X_SAT      = 0x0400,
            S_ACC_X_DEC_SAT  = 0x0200,
            S_ACC_X_INTP_SAT = 0x0100,
            S_ACC_X_STC_DIG  = 0x0080,
            S_ACC_X_STC_TCAP = 0x0040,
            S_ACC_X_STC_SDD  = 0x0020,
            S_ACC_X_STC_N    = 0x0010,
            S_ACC_X_SD_STS   = 0x0004,
            S_ACC_X_STS      = 0x0002,
            S_ACC_X_STS_RDY  = 0x0001,

            /**
             * ACC Status Y Register bit definitions
             */
            S_ACC_Y_SAT      = 0x0400,
            S_ACC_Y_DEC_SAT  = 0x0200,
            S_ACC_Y_INTP_SAT = 0x0100,
            S_ACC_Y_STC_DIG  = 0x0080,
            S_ACC_Y_STC_TCAP = 0x0040,
            S_ACC_Y_STC_SDD  = 0x0020,
            S_ACC_Y_STC_N    = 0x0010,
            S_ACC_Y_SD_STS   = 0x0004,
            S_ACC_Y_STS      = 0x0002,
            S_ACC_Y_STS_RDY  = 0x0001,

            /**
             * ACC Status Z Register bit definitions
             */
            S_ACC_Z_SAT      = 0x0400,
            S_ACC_Z_DEC_SAT  = 0x0200,
            S_ACC_Z_INTP_SAT = 0x0100,
            S_ACC_Z_STC_DIG  = 0x0080,
            S_ACC_Z_STC_TCAP = 0x0040,
            S_ACC_Z_STC_SDD  = 0x0020,
            S_ACC_Z_STC_N    = 0x0010,
            S_ACC_Z_SD_STS   = 0x0004,
            S_ACC_Z_STS      = 0x0002,
            S_ACC_Z_STS_RDY  = 0x0001
        } reg_bitmask;

    public:
        bool transportHealthy() const { return !_transportError; }
        int         begin(SCH16T_filter sFilter, SCH16T_sensitivity sSensitivity, SCH16T_decimation sDecimation, bool enableDRY = false);
        void        getData(SCH16T_raw_data *data);
        void        getDataDecimated(SCH16T_raw_data *data);
        void        getDataAux(SCH16T_raw_data *data);
        void        convertData(SCH16T_raw_data *data_in, SCH16T_result *data_out);
        void        convertDataDecimated(SCH16T_raw_data *data_in, SCH16T_result *data_out);
        void        convertDataAux(SCH16T_raw_data *data_in, SCH16T_result *data_out);

        int         setFilters(uint32_t Freq_Rate12, uint32_t Freq_Acc12, uint32_t Freq_Acc3);
        int         setRateSensDec(uint16_t Sens_Rate1, uint16_t Sens_Rate2, uint16_t Dec_Rate2);
        int         getRateSensDec(uint16_t *Sens_Rate1, uint16_t *Sens_Rate2, uint16_t *Dec_Rate2);
        int         setAccSensDec(uint16_t Sens_Acc1, uint16_t Sens_Acc2, uint16_t Sens_Acc3, uint16_t Dec_Acc2);
        int         getAccSensDec(uint16_t *Sens_Acc1, uint16_t *Sens_Acc2, uint16_t *Sens_Acc3, uint16_t *Dec_Acc2);
        int         setDRY(int8_t polarity, bool enable);
        int         enableMeas(bool enableSensor, bool setEOI);

        void        reset(void);
        void        sendSPIreset(void);
        bool        verifyStatus(SCH16T_status *Status);
        int         getStatus(SCH16T_status *Status);
        char        *getSnbr(void);

    protected:
        SCH16T(spi_device_handle_t spi, int cs_pin, int reset_pin = -1, int ta9_8 = 0);

    private:
        uint32_t            convertRateFilterToBitfield(uint32_t Freq);
        uint32_t            convertAccFilterToBitfield(uint32_t Freq);
        virtual uint32_t    convertRateSensToBitfield(uint32_t Sens);
        virtual uint32_t    convertBitfieldToRateSens(uint32_t bitfield);
        uint32_t            convertAccSensToBitfield(uint32_t Sens);
        uint32_t            convertBitfieldToAccSens(uint32_t bitfield);
        uint32_t            convertDecimationToBitfield(uint32_t Decimation);
        uint32_t            convertBitfieldToDecimation(uint32_t bitfield);

        bool                isValidRateFilterFreq(uint32_t Freq);
        bool                isValidAccFilterFreq(uint32_t Freq);
        bool                isValidSampleRate(uint32_t Freq);
        virtual bool        isValidRateSens(uint32_t Sens);
        bool                isValidAccSens(uint32_t Sens);
        bool                isValidDecimation(uint32_t Decimation);

        int32_t     SPI48_DATA_INT32(uint64_t a) { return YuEEGSafeSpi::signed20(a); }
        uint16_t    SPI48_DATA_UINT16(uint64_t a) { return (uint16_t)(((a) >> 8)  & 0x0000ffffUL); }
        bool        checkCRC8(uint64_t SPIframe);
        bool        checkCRC3(uint32_t SPIframe);
        uint8_t     CRC8(uint64_t SPIframe);
        uint8_t     CRC3(uint32_t SPIframe);
        bool        check48bitFrameError(uint64_t *data, int size);
        uint64_t    sendRequest(uint64_t Request);
        uint64_t    addTargetAddress(uint64_t Request);
        uint64_t    addTargetAddressNoCRC(uint64_t Request);

        spi_device_handle_t _spi;
        bool _transportError=false, _havePrevious=false;
        uint64_t _lastRequest=0;
        int _cs, _reset;
        uint8_t _ta9_8;
        int _sens_rate1, _sens_rate2, _sens_acc1, _sens_acc2, _sens_acc3;
};

class SCH16T_K01 : public SCH16T {
    public:
        SCH16T_K01(spi_device_handle_t spi, int cs_pin, int reset_pin = -1, int ta9_8 = 0);
};

class SCH16T_K10 : public SCH16T {
    public:
        SCH16T_K10(spi_device_handle_t spi, int cs_pin, int reset_pin = -1, int ta9_8 = 0);
        bool        isValidRateSens(uint32_t Sens);
        uint32_t    convertRateSensToBitfield(uint32_t Sens);
        uint32_t    convertBitfieldToRateSens(uint32_t bitfield);
};

#endif

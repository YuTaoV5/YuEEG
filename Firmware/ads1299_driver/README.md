# YuEEG Rev H development firmware (ESP32-S3-WROOM-1U-N16R8)

Rev H keeps simultaneous isolated USB CDC + Wi-Fi UDP, CO5300 AM178 AMOLED status and SDMMC backup. The board uses a removable Sony NP-BX1 single-cell battery through a protected 5V boost supply. The battery is removed for charging in its dedicated external charger. Acquisition GPIO assignments and the 50-byte protocol remain unchanged. Rev G source and binaries remain frozen in `hardware/YuEEG_8CH_RevG/firmware/`; this development firmware has not been flashed or tested on a physical Rev H assembly.

## Build

Arduino ESP32 core 2.0.11; no third-party display library is required. Select ESP32S3 Dev Module, 16 MB QIO flash, OPI PSRAM, Hardware CDC/JTAG USB mode, USB CDC on boot, and `app3M_fat9M_16MB` partitioning. Open `ads1299_driver.ino`.

```powershell
arduino-cli compile --fqbn "esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB" Firmware/ads1299_driver
```

## Interfaces

| Function | GPIO |
|---|---|
| ADS1299 SPI2 CS / SCLK / MOSI / MISO | 10 / 12 / 11 / 13 |
| ADS DRDY / RESET / PWDN / START | 4 / 5 / 6 / 7 |
| Native USB DM / DP | 19 / 20 |
| AMOLED SPI3 CS / CLK / D0 / D1 / D2 / D3 | 2 / 8 / 9 / 14 / 15 / 16 |
| AMOLED RESET / power-enable | 17 / 42 |
| SDMMC CLK / CMD / DAT0 / card detect | 18 / 21 / 47 / 48 |
| REC key (active low) | 41 |
| RUN / Wi-Fi / FAULT LEDs (active low) | 38 / 39 / 40 |
| NP-BX1 protected loaded-voltage ADC1_CH0 | 1 |

GPIO35/36/37 remain reserved for OPI PSRAM. Hardware RESET, BOOT and REC use ALPS SKRTLBE010 side-actuated switches. REC retains 30 ms firmware debounce.

## Acquisition and control

500 SPS, gain 12 by default; external shared REF, bipolar analog rails, BIAS feedback. Boot waits 10 seconds after PWDN release, checks ADC ID, and remains stopped. Press REC or send `start`; press again or send `stop`. Other USB commands: `test`, `probe 1..8`, `gain 1/2/4/6/8/12/24`, `udp IP PORT`, `wifi SSID<TAB>PASSWORD`, `status`. Electrode probe is an excited-loop observation, not a calibrated independent contact-impedance measurement.

AP credentials are generated randomly and stored in NVS; USB `status` reports them. UDP data defaults to 192.168.4.255:9000. UDP control on port 9001 requires `YEEG <AP-password> <command>`; use `Firmware/tools/send_eeg_command.py`. Keep the password private. ADC configuration always executes in the acquisition task; the network task only queues commands.

## AMOLED

Use OSPTEK AM178Q368448LK **CO5300 QSPI**, 368 x 448. Rev H places the display power/logic circuits and OCN OK-14F024-04 female J2002 on the digital board. The former Rev G carrier cable and 10mm standoff arrangement do not apply. Screen FPC reach and the final raised-screen connection remain unresolved; see `docs/REVH_MECHANICAL_REVIEW.md`.

The load switch supplies module VBAT at 3.3 V; IOVCC is 1.8 V through the existing SN74AXC8T245 level translator. IM1 is unused; touch remains held in reset. CO5300 register settings and x-gap=16 are adapted from the supplied OSPTEK example (see THIRD_PARTY_DISPLAY.md). Firmware uses RGB565, sets a bounded 368 x 448 window, starts at brightness 0x40, and disables TE. RESET is held low before power-up, then released after settling. First-article power/initialization validation is still required.

SPI3 at 10 MHz is separate from ADS SPI2. A low-priority task updates status once per second using an internal DMA buffer; no touch, TE synchronization or waveform renderer is implemented. `panel_bus=OK` means transactions were accepted by the ESP controller: this write-only path cannot identify or confirm a working panel. SPI/SD activity and Wi-Fi coupling must be measured during noise qualification.

## microSD backup

Insert a formatted FAT32 card before power-up. Mount at 20 MHz in SDMMC 1-bit mode, with no automatic formatting. Backup is enabled once mounting succeeds; absent media or allocation/mount failure leaves USB and UDP acquisition operational. Recovery after card removal/write error requires reboot. Card detect is available in hardware; hot-plug recovery is not implemented.

Every outgoing 50-byte raw frame is offered to a 128 KiB PSRAM stream buffer without blocking. A lower-priority writer writes `/eeg_000001.yee`, then the next unused name, and so on. Files are closed after stop and buffer drain; CRC and sequence metadata remain unchanged. Buffer overflow or write failure increments `sd_drop`; `saved` counts fully written frames, not a durability guarantee. SD stalls and sudden power loss can lose buffered or unflushed data. Allow at least one second after stopping before removing power/card. A short initial acquisition before mount completes is not backed up; check `SD READY` first.

```powershell
python Firmware/tools/receive_eeg.py --file eeg_000001.yee > samples.csv
python Firmware/tools/receive_eeg.py --udp 9000 > samples.csv
python Firmware/tools/receive_eeg.py --serial COM8 --command start > samples.csv
python Firmware/tools/test_protocol.py
```

Only serial reception requires `pyserial`. The six protocol tests include signed 24-bit limits, CRC rejection/resynchronization, fragmented input, UDP batching, gain scaling and offline SD-file conversion/EOF.

## Frame and validation scope

50 bytes: `YEEG`, version 1, mode, gain, probe channel, sequence LE32, device timestamp-us LE32, missed-DRDY LE32, ADS status + eight signed 24-bit big-endian samples (27 bytes), flags, CRC16-CCITT (initial FFFF, first 48 bytes, LE16). Conversion assumes 4.5 V ADC reference. USB/UDP queue drops and storage drops are reported separately. The CRC detects transmission/storage corruption; it does not detect every missed sample.

The firmware has compile and host-protocol checks. No physical board has yet verified flash/USB, simultaneous wireless + backup, display startup, SD stalls, analog noise or patient isolation. Use the hardware review and bench checklist before attaching electrodes.

## Rev H power and electrodes

Use the user-selected Sony NP-BX1 single-cell battery and a matching external dedicated charger. Rev H has no on-board charging input or cell-midpoint connector. Power-strip JP2 to digital JH2 is 1=SYS_5V, 2=BAT_PROTECTED_SENSE, 3/4=GND. Pin 2 is not a parallel 5V supply pin. The USB data port remains isolated and does not supply the acquisition electronics; a battery or a suitable isolated bench supply is required.

Physically unplug the entire 10-electrode harness (CH1..8, REF and BIAS) before charging. Turn acquisition off before connecting the charger. Firmware cannot verify a detached electrode cable. A stopped ADC or a software command is not an electrode disconnect. Main J1301 pin order is 1 REF, 2 BIAS, 3 CH8, 4 CH7, 5 CH6, 6 CH5, 7 CH4, 8 CH3, 9 CH2, 10 CH1. REF is the shared measurement reference; BIAS is a driven common-mode electrode, not protective earth.

The acquisition slide switch disables the protected battery supply. Remove the battery for charging. The exposed J301 pogo interface is nonisolated bench access: disconnect electrodes before using it. Firmware cannot verify electrode removal or certify USB isolation.

## NP-BX1 voltage telemetry

`YuEEG_Battery.h` samples GPIO1 / ADC1_CH0 in a separate priority-1 task on core 0 once per second. It takes 16 millivolt readings with 2ms spacing, discards one minimum and one maximum, and applies the nominal R309=330k / R310=100k divider. ADC work never runs in the DRDY ISR or the acquisition loop. The panel and USB/UDP `status` report `CELL nnnn MV OK/LOW`, or `CELL UNAVAILABLE` for an implausible input or absent reading.

The low warning sets at a measured protected supply of 3450mV and clears at 3550mV. It lights the FAULT LED but does not stop capture or alter the 50-byte frame format. Hardware undervoltage protection remains independent. Stop acquisition and allow SD writes to finish before removing power when the low warning appears; firmware cannot guarantee a flush before the hardware supply cuts off.

This reading is **loaded voltage after the fuse, reverse MOSFET and eFuse**, not open-circuit cell voltage or charge percentage. The software accepts 2700–4400mV as a plausibility window; that window is not a battery operating specification. Core 2.0.11 provides `analogReadMilliVolts` and `ADC_2_5db`; nominal divider tolerances and ADC accuracy still require board calibration against a meter at several voltages and loads. No runtime, SOC or first-article accuracy claim is made.

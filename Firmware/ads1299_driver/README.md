# YuEEG Rev E firmware (ESP32-S3-WROOM-1-N16R8)

Rev E adds an RM67162 AMOLED status panel, SDMMC backup, and a REC key to the existing simultaneous isolated USB CDC + Wi-Fi UDP acquisition path. Rev D's exact source and binaries remain frozen in `hardware/YuEEG_8CH_RevD/firmware`.

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

GPIO35/36/37 remain reserved for OPI PSRAM. Hardware RESET and BOOT use 0.53 mm Panasonic EVPBB2A9B000 switches; REC uses the same part and 30 ms firmware debounce.

## Acquisition and control

500 SPS, gain 12 by default; external shared REF, bipolar analog rails, BIAS feedback. Boot waits 10 seconds after PWDN release, checks ADC ID, and remains stopped. Press REC or send `start`; press again or send `stop`. Other USB commands: `test`, `probe 1..8`, `gain 1/2/4/6/8/12/24`, `udp IP PORT`, `wifi SSID<TAB>PASSWORD`, `status`. Electrode probe is an excited-loop observation, not a calibrated independent contact-impedance measurement.

AP credentials are generated randomly and stored in NVS; USB `status` reports them. UDP data defaults to 192.168.4.255:9000. UDP control on port 9001 requires `YEEG <AP-password> <command>`; use `Firmware/tools/send_eeg_command.py`. Keep the password private. ADC configuration always executes in the acquisition task; the network task only queues commands.

## AMOLED

Use DWO DO0200PFS12 **RM67162 variant**, 240 x 536, configured for QSPI (IM1 high, module R4 fitted/R3 absent). Confirm the supplier's exact initialization and connector orientation before purchasing. A verified 18-way harness connects the module to J1001; the pitch alone does not establish connector compatibility.

The load switch enables module VBAT, a 2.8 V regulator supplies VCC and a 1.8 V regulator supplies IOVCC. The SN74AXC8T245 translates the seven write-only control/data lines. Firmware sets input states before enabling power, releases RESET after rail settling, uses RGB565 and starts at reduced brightness. The QSPI register framing and common RM67162 commands follow the primary Arduino_GFX driver; manufacturer-specific initialization remains a first-article check.

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

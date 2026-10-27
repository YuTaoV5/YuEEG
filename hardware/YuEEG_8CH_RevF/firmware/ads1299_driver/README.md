# YuEEG Rev F firmware (ESP32-S3-WROOM-1-N16R8)

Rev F keeps simultaneous isolated USB CDC + Wi-Fi UDP, RM67162 AMOLED status and SDMMC backup. The main board runs from its protected 2S battery; its detached isolated charger never powers acquisition directly. GPIO assignments and the 50-byte protocol are unchanged from Rev E. Rev D/E source and binaries remain frozen in their hardware review folders.

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

GPIO35/36/37 remain reserved for OPI PSRAM. Hardware RESET, BOOT and REC use ordinary C&K PTS645SM43SMTR92 LFS 6 x 6 mm SMT tactile switches (4.3 mm high). REC retains 30 ms firmware debounce.

## Acquisition and control

500 SPS, gain 12 by default; external shared REF, bipolar analog rails, BIAS feedback. Boot waits 10 seconds after PWDN release, checks ADC ID, and remains stopped. Press REC or send `start`; press again or send `stop`. Other USB commands: `test`, `probe 1..8`, `gain 1/2/4/6/8/12/24`, `udp IP PORT`, `wifi SSID<TAB>PASSWORD`, `status`. Electrode probe is an excited-loop observation, not a calibrated independent contact-impedance measurement.

AP credentials are generated randomly and stored in NVS; USB `status` reports them. UDP data defaults to 192.168.4.255:9000. UDP control on port 9001 requires `YEEG <AP-password> <command>`; use `Firmware/tools/send_eeg_command.py`. Keep the password private. ADC configuration always executes in the acquisition task; the network task only queues commands.

## AMOLED

Use DWO DO0200PFS12 **RM67162 variant**, 240 x 536, configured for QSPI (IM1 high, module R4 fitted/R3 absent). Confirm the supplier's exact initialization and connector orientation before purchasing. Main J1001 is a dedicated keyed Samtec FTSH-110 20-pin display connector, not JTAG. A verified custom 20-to-18 harness connects its first 18 electrical functions to module CN1; main pins 19/20 are extra GND. Safely terminate/insulate unused conductors. Connector pitch alone does not establish module compatibility. The module uses four nominal 8 mm insulated standoffs above the main board.

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

## Rev F power and electrodes

Use a matched 2S 4.2 V/cell Li-ion pack of at least 1000 mAh with the specified 10k NTC and cell-midpoint connection. Main J1202 and charger J1204 use a verified GH6 cable: 1 PACK_POS, 2 GND, 3 CHG_TS, 4 CHG_CE, 5 USB5, 6 CHG_PG. These are all isolated secondary signals. This is not a USB cable or a general-purpose expansion port. The main DATA Type-C has data isolation and cannot boot or charge the board without a battery. The daughterboard CHARGE Type-C has no data.

Physically unplug the entire 10-electrode harness (CH1..8, REF and BIAS) before charging. Turn acquisition off before connecting the charger. Firmware cannot verify a detached electrode cable. A stopped ADC or a software command is not an electrode disconnect. Main J1301 pin order is 1 REF, 2 BIAS, 3 CH8, 4 CH7, 5 CH6, 6 CH5, 7 CH4, 8 CH3, 9 CH2, 10 CH1. REF is the shared measurement reference; BIAS is a driven common-mode electrode, not protective earth.

The acquisition slide switch controls the battery power gate. After switching off, input capacitors discharge through the 47k bleeder and other loads before the charger's CE input permits charging; allow approximately 10–15 seconds, subject to measured discharge behavior. Charging is nominally 8.2 V / 299 mA, with charger tolerances and the selected cell/NTC requirements to be checked before first charge. The exposed J301 pogo interface is nonisolated bench access: disconnect electrodes before using it.

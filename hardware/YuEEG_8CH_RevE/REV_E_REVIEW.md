# Rev E design review

## Requested changes and resulting design

Rev E separates DATA/FLASH and CHARGE/POWER into two USB-C receptacles on the same board edge. The 1.91 inch AMOLED, microSD backup, grouped status LEDs, 0.53 mm RESET/BOOT/REC switches, rounded outline and rounded silkscreen module frames replace the former expansion-header layout. The board is 94 x 122 mm, four layers. Rev D remains frozen as a reproducible previous design.

The 56 x 35 mm initial target was already exceeded by the isolated power/data and 2S battery design. Rev E adds a 26.4 x 57.52 mm module with mounting hardware; the extra 10 mm of width permits a dedicated display strip while preserving the existing analog layout and 8 mm isolation moat. This is an engineering integration board, not a miniature production headset.

## USB and battery topology

J601 DATA/FLASH VBUS -> 500 mA hold resettable fuse F901 -> DATA_5V powers only the upstream ADuM4160 side. J601 CC1/CC2 have independent 5.1 kohm Rd. J901 CHARGE/POWER VBUS -> HOST_RAW -> existing 1.5 A hold PTC F701 -> HOST_5V. Its CC pins go to TUSB320 so isolated power is enabled only when the source advertises 1.5 A or 3 A. The two VBUS nets are never joined or ORed. Both connector shields/grounds remain on HOST_GND, isolated from electrode/system GND.

ADuM4160 supplies full-speed USB data isolation; THM6-0511 supplies isolated power through the current-limited switch. Native ESP32-S3 USB Serial/JTAG supports flashing and binary CDC streaming; Wi-Fi UDP operates concurrently. DATA alone needs a charged battery and POWER ON. CHARGE/POWER alone has no USB data. A suitable CHARGE supply plus POWER ON powers the system through the existing interlocked SYS path. POWER OFF permits approximately 299 mA, 8.2 V 2S charging with 10 kohm NTC; POWER ON inhibits charging. A data cable does not bypass the charge/current gates.

The two-cell pack is not selected: design assumes matched 4.2 V Li-ion/polymer cells, at least 1000 mAh, insulated 10 kohm NTC. Protection, balancing and charger remain from Rev D. Final charge current, temperature limits, cell placement and pack harness require the actual cell datasheet. Isolation components and an 8 mm copper rule do not establish patient leakage/dielectric compliance of an assembled product.

## EEG inputs and analog path

CH1..8 expose the positive wet electrode input, with a shared external REF distributed to the eight negative paths through the existing resistor/filter networks. BIAS is the actively driven common-mode electrode, not the negative channel input and not a direct ground electrode. Electrode placement is a measurement protocol choice; the board's labels do not prescribe vertex placement.

Analog rails remain +2.5 V and -2.5 V relative to system GND. The ADS1299 internal 4.5 V reference spans relative to AVSS; this must not be confused with the supply or scalp REF electrode. The BIAS midpoint is near system GND under symmetric rails.

J801/J802/J803 and their sixteen bypass links are removed. Both polarities now use the original direct two-stage 4.99 kohm + 4.99 kohm protection/filter paths, rail clamps and matched differential capacitance. External buffering is not silently inserted into one polarity. Wet-electrode contact impedances vary with skin preparation and location; hardware matching means matching transfer functions and input bias-current paths, rather than terminating an electrode to a nominal resistor value. REF/BIAS and channel inputs retain their current-limiting/clamp networks. Small-signal clamp parts are not a defibrillator-protection claim.

## AMOLED supply, signals and mounting

Selected module: DWO DO0200PFS12, **RM67162 version**, 240 x 536, 1.91 inch, 26.4 x 57.52 x 5.38 mm with integrated display power generation. Procurement must lock this controller and QSPI configuration (IM1 high, R4 fitted/R3 absent); the datasheet also permits other variants. Do not substitute a bare panel or SH8501 module.

The module specifies VBAT 2.9..4.5 V, VCC 2.7..3.36 V and IOVCC 1.72..3.4 V. Because the existing digital rail's conservative upper budget exceeds 3.4 V, directly using it for all three pins is not accepted. TPS22918 switches raw module power; TPS7A2028 and TPS7A2018 provide 2.8 V and 1.8 V. SN74AXC8T245 supplies A-to-B translation for CS/CLK/D0..3/RESET, with output-disable pull-up, power-enable-controlled transistor and safe input defaults. Seven 22 ohm output resistors damp edges. Ioff/VCC isolation prevents the unpowered side being driven through ordinary logic inputs.

J1001 is Molex Panelmate 53780-1870, 18 pins at 1.25 mm. The module drawing specifies CN1 pitch/pin count, not a guaranteed mating family: **a verified custom harness is required**, with pin 1 and contact-side orientation confirmed. CN1 pins 4, 13..15 and 17 are unused; touch RESET is held low, touch is not implemented. TE is unused. Firmware is write-only QSPI on SPI3, separate from ADS SPI2; a controller-level success does not verify panel response.

The display occupies x=72..98.4, y=108.04..165.56 in absolute board coordinates. Four M2 mounting holes use 6 mm insulated standoffs, clearing the rear UI electronics and keeping the front module clear of the electrode connector column. Check actual module hole size, screws, harness bend, component heights and the enclosure on a first article. The original VRML models are approximate envelopes; the screen graphic is a layout preview, not acquired EEG.

## Storage and controls

Hirose DM3AT-SF-PEJM5 microSD socket is on the rear, with the card opening toward the right board edge. The footprint drawing shows an ejected-card envelope to approximately x=166.7 mm, 2.7 mm beyond the board; reserve this travel and a finger access opening in the enclosure. The 3D card represents the ejected envelope. SDMMC uses CLK18/CMD21/DAT0 47; CD48 is available. CMD and **all four DAT pins**, including unused DAT1..3, have 10 kohm pull-ups as required by Espressif. A ferrite bead and local 22 uF/1 uF/100 nF capacitors supply the card; two USBLC6-2 devices protect used signal lines. Clock has 22 ohm source damping. Board-level ESD performance remains a test item.

Firmware uses 1-bit SDMMC at 20 MHz and a 128 KiB PSRAM buffer; it never blocks the sample output task waiting for the card. It saves unchanged CRC-protected 50-byte frames to uniquely named .yee files, reports dropped frames, and provides an offline CSV decoder. No card formatting or hot-plug recovery is implemented. Mount, allocation, card stalls and power loss can prevent complete backup; check SD READY before starting.

RESET, BOOT and REC are Panasonic EVPBB2A9B000, 2.6 x 1.6 x 0.53 mm. The custom footprint follows the four-pad manufacturer land pattern with the two pads on each side electrically common. Copper/pad/via restrictions under the metal pressure plate are retained; REC has external pull-up, RC suppression and 30 ms software debounce. Use an enclosure actuator designed for the supplier's allowed stroke and load; a thin switch is not an adhesive membrane keypad.

## Primary sources

- [Espressif ESP32-S3 DevKitC-1 user guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html): separating USB functions; this reference uses micro-USB, not the two Type-C implementation on this board.
- [LilyGO AMOLED projects](https://github.com/Xinyuan-LilyGO/LilyGo-AMOLED-Series): display bus, controller and power-design comparisons. Its common-ground development boards are not copied across the EEG isolation barrier.
- [DWO DO0200PFS12 module datasheet](https://18746902.s21i.faimallusr.com/61/1/ABUIABA9GAAgxZGgswYo8vqOygc.pdf): supply limits, module mechanics, connector pins and mode straps.
- [Panasonic EVPBB manufacturer drawing](https://industrial.panasonic.com/cdbs/www-data/pdf/ATK0000/ATK0000COS4189.pdf): switch dimensions and PCB pattern.
- [TI SN74AXC8T245](https://www.ti.com/lit/ds/symlink/sn74axc8t245.pdf), [TPS7A20](https://www.ti.com/lit/ds/symlink/tps7a20.pdf), [TPS22918](https://www.ti.com/lit/ds/symlink/tps22918.pdf): pin functions, power sequencing and voltage translation.
- [Espressif SD pull-up requirements](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/sd_pullup_requirements.html): CMD/DAT pull-ups in 1-bit operation.
- [ST USBLC6-2](https://www.st.com/resource/en/datasheet/usblc6-2.pdf): rail-clamp topology and pin assignments.
- [Arduino_GFX RM67162 driver](https://github.com/moononournation/Arduino_GFX/blob/master/src/display/Arduino_RM67162.h): common QSPI RGB565 startup commands. The Rev E driver is an independent implementation; supplier-specific panel initialization still needs first-article confirmation.

## Release evidence and first-article requirements

See `review/PCB_validation.json`, the exact native ERC/DRC reports, independent pin audits, connection report and firmware BUILD_INFO for the released bytes. Automated checks establish static connectivity, design-rule compliance and compilation only. Measure analog rails/startup, reference/BIAS stability, input-referred noise, USB signal integrity, simultaneous Wi-Fi/USB/SD capture, charger faults/thermals and isolation before human-use consideration. Check every mechanical part against the supplier drawing and review filled/capped via-in-pad processing with the board house.

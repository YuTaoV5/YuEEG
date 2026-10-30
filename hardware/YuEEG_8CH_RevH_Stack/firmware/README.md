# Rev H firmware engineering snapshot

This snapshot matches the current NP-BX1 hardware wiring. It includes isolated USB + Wi-Fi output, SD backup, AMOLED status and a separate ADC1 battery telemetry task. Six host protocol tests and the ESP32-S3 build passed; no Rev H board has been flashed or measured.

`build/BUILD_INFO.json` binds the sources and binary hashes. Read `ads1299_driver/README.md` for exact GPIOs, build settings and limitations. Battery telemetry is protected loaded voltage with nominal divider scaling, not SOC or calibrated cell voltage. The warning does not guarantee an SD flush before hardware cutoff.

Rev G sources and binaries remain in their own frozen hardware folder. This folder is development evidence, not a production firmware release.

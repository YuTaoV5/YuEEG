# Rev H mechanical evidence and experiments

The authoritative electrical boards remain `../../afe`, `../../digital`, and `../../power`. Their engineering exports are outside this folder. This folder is not a manufacturing package.

- `screen_envelope_review.*`: conditional screen/connector envelope analysis; not a measured FPC or completed assembly.
- `pogo_reference.*`: manufacturer probe dimensions and third-party NP-BX1 sample contact geometry; not a qualified battery holder.
- `battery_side_envelope.*`: conservative XY battery/header/HOST-domain screening for the selected architecture. A battery on the right with a provisional 6 mm board-edge gap is proposed; this is not a completed assembly, enclosure or certified isolation check.
- The user chose to retain USB isolation on the digital board and accepts a stack larger than the display. Unselected USB relocation experiments and their electrical drafts have been removed from this current folder and archived locally; the published placement experiment remains traceable through commit `e1f0457`.

Read [USB layout decision and history](../../../../docs/REVH_COMPACT_USB_PARTITION.md). USB isolation stays on the digital board; no FH12 USB cable is part of the selected design. The digital PH4 was subsequently changed to a right-facing through-hole header. Its current source/pad extraction, cable reservation and tail constraints are in `power_ports_native.json`, `power_harness_routing_review.json` and `power_port_tail_review.json`.

`afe_host_screen.json` and `usb_mouth_review.json` describe the later AFE copper exclusion and USB board-edge changes. `display_link/review/fold_space.json` covers the passive display-link prototype, with R1101's low-height MPN now selected in the main BOM. These conditional checks do not resolve the battery contact interface or the factory screen-back datum.

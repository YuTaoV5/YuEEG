# Rev H mechanical evidence and experiments

The authoritative electrical boards remain `../../afe`, `../../digital`, and `../../power`. Their engineering exports are outside this folder. This folder is not a manufacturing package.

- `screen_envelope_review.*`: conditional screen/connector envelope analysis; not a measured FPC or completed assembly.
- `pogo_reference.*`: manufacturer probe dimensions and third-party NP-BX1 sample contact geometry; not a qualified battery holder.
- `battery_side_envelope.*`: conservative XY battery/header/HOST-domain screening for the selected architecture. A battery on the right with a provisional 6 mm board-edge gap is proposed; this is not a completed assembly, enclosure or certified isolation check.
- The user chose to retain USB isolation on the digital board and accepts a stack larger than the display. Unselected USB relocation experiments and their electrical drafts have been removed from this current folder and archived locally; the published placement experiment remains traceable through commit `e1f0457`.

Read [USB layout decision and history](../../../../docs/REVH_COMPACT_USB_PARTITION.md). The active boards and their original PH4 power/telemetry cable are unchanged; no FH12 USB cable is part of the selected design.

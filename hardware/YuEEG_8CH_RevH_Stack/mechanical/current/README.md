# Rev H mechanical evidence and experiments

The authoritative electrical boards remain `../../afe`, `../../digital`, and `../../power`. Their engineering exports are outside this folder. This folder is not a manufacturing package.

- `screen_envelope_review.*`: conditional screen/connector envelope analysis; not a measured FPC or completed assembly.
- `pogo_reference.*`: manufacturer probe dimensions and third-party NP-BX1 sample contact geometry; not a qualified battery holder.
- `usb_partition_feasibility.json`: native-net partition analysis for a possible USB relocation.
- `usb_power_fit_candidate.kicad_pcb/.kicad_pro/.kicad_dru`: **UNROUTED PLACEMENT EXPERIMENT**, 43×23.6 mm, 37 parts, 9 back SMT. Not a replacement for the power board. Old temporary JP1/PH4 remain; new cable and probe pads are absent. No schematic/parity, routing, ground plane or manufacturing output.
- `usb_power_fit_candidate.json`, `usb_power_fit_drc.json`, `usb_power_fit_overview.*`: evidence and drawing for that experiment. Native placement DRC has zero violations and **88 unconnected items**. This does not prove electrical function, assembly, USB impedance, safe isolation or overall size reduction.

Read [compact partition assessment](../../../../docs/REVH_COMPACT_USB_PARTITION.md) before opening or reusing the candidate. Its library table and model paths are relative to this experiment folder.

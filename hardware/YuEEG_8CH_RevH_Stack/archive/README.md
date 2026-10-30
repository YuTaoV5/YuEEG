# Local development history

Earlier 2S power boards, interface migrations and pre-mounting-hole copies are retained locally under this directory. They are superseded and are not part of the published Rev H engineering checkpoint. The GitHub view keeps current native sources and current bound reports; published Rev D/E/F/G releases remain in their own frozen directories.

Do not use old 2S power snapshots with the user-selected NP-BX1 battery.

`usb_relocation_not_selected/` retains local placement/electrical experiments for moving USB onto the battery power strip. The user explicitly chose to retain USB isolation and Type-C on the digital board and accepts a stack larger than the screen. These experiments and their 12-pin FH12 proposal are not part of the selected circuit or manufacturing exports. The published placement snapshot can be traced through commit `e1f0457`; the later electrical draft was never released.

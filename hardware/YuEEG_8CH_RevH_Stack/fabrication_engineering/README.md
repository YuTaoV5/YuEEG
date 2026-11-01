# Rev H engineering Gerber / drill / SMT export

**NOT FOR ORDER — mechanical and sourcing gates remain open.** These files are for engineering review, not a released production package. No order ZIP is generated.

Digital now includes SCH16T-K01-1: 129 electrical references, 25 backside SMT parts. The sensor footprint carries a six-copper-layer underbody pour keepout, with routed ground returns. SPI2/USB sampled plane coverage is unchanged; local control/display return and noise behavior remains unmeasured. Do not refill copper into the underbody void in CAM. All three main boards total285 electrical references /286 physical components. The IMU regulator and input capacitor overlap the AFE C220 projection; require measured local surface gap >=8.3mm, mounted C220 <=6.2mm and mounted upper parts <=1.55mm. This is an assembly acceptance condition, not a qualified tolerance stack. Firmware implements continuous relative attitude and explicitly aligned3s relative trajectory, with USB/UDP9002 and separate SD backup; noUWB, absolute yaw or long-term position guarantee. Hardware validation remains open.

AFE: 48×60mm, four copper layers. Digital: 48×60mm, six copper layers. Power strip: 34×18mm, two copper layers. AFE/digital thickness is 1.6mm; the integrated probe power board is nominal 1.0mm with an explicit two-copper-layer stackup.

AFE and digital each have three 2.4mm round internal openings at (44,4), (44,51), (4,55), represented in **Edge.Cuts**. They are not duplicated as Excellon drill hits. CAM must preserve all three internal circles. M2 mounting screws, spacers and washers must be insulating.

JP1 is now a routed 10mm pair of B-side Mill-Max 0906 probes, D+/B- confirmed by the user; BOM Quantity=2 at JP1. Holder stops, compression/tolerances, delivered-part matching, full 3D harness and screen support remain unqualified. The user confirmed display connector procurement. The user explicitly authorized derived probe dimensions, diagrams, hashes and resultingPCB/docs publication on2026-11-01; originalSTEP/JPG are excluded. Read `docs/REVH_MECHANICAL_REVIEW.md` and `docs/REVH_NPBX1_POWER.md` before using these exports.

Digital JH2 is now the right-facing TH S4B-PH-K-S. Trim/inspect its solder and tails to <=1.2mm below B; follow docs/REVH_POWER_HARNESS.md.

Front/back SMT positions are exported separately; hand-assembled through-hole connectors, probes and mounting hardware are not an SMT-only placement file. BOM lists and manufacturing stackup/impedance, thermal-via and assembly-process requirements must be reviewed before an actual fabrication release. Clean static checks do not prove assembly, functional acquisition or patient isolation.

`MANIFEST.json` binds each export to its current PCB hash. Regenerate this directory after any board change.

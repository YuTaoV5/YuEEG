# Rev H engineering Gerber / drill / SMT export

**NOT FOR ORDER — mechanical and sourcing gates remain open.** These files are for engineering review, not a released production package. No order ZIP is generated.

Digital now includes SCH16T-K01-1: 129 electrical references, 26 backside SMT parts (including the SMT mezzanine plug). The sensor footprint carries a six-copper-layer underbody pour keepout, with routed ground returns. The SMT interboard pair is0.8mm/20contacts/8.5mm mated height, replacing pin headers. CurrentSPI2 centerline screening is recorded separately; control/display return and noise behavior remains unmeasured. Exact Taobao pair SKU remains unconfirmed. Do not refill copper into the underbody void in CAM. All three main boards total285 electrical references /286 physical components. The IMU regulator and input capacitor overlap the AFE C220 projection; require measured local surface gap >=8.3mm, mounted C220 <=6.2mm and mounted upper parts <=1.55mm. This is an assembly acceptance condition, not a qualified tolerance stack. Firmware implements continuous relative attitude and explicitly aligned3s relative trajectory, with USB/UDP9002 and separate SD backup; noUWB, absolute yaw or long-term position guarantee. Hardware validation remains open.

AFE: 48×60mm, four copper layers. Digital: 48×60mm, six copper layers. Power strip: 34×18mm, two copper layers. AFE/digital thickness is 1.6mm; the integrated probe power board is nominal 1.0mm with an explicit two-copper-layer stackup.

AFE and digital each have three 2.4mm round internal openings at (44,4), (44,51), (4,55), represented in **Edge.Cuts**. They are not duplicated as Excellon drill hits. CAM must preserve all three internal circles. M2 mounting screws, spacers and washers must be insulating.

JP1 is now a routed 10mm pair of B-side Mill-Max 0906 probes, D+/B- confirmed by the user; BOM Quantity=2 at JP1. Holder stops, compression/tolerances, delivered-part matching, full 3D harness and screen support remain unqualified. The user confirmed display connector procurement. The user explicitly authorized derived probe dimensions, diagrams, hashes and resultingPCB/docs publication on2026-11-01; originalSTEP/JPG are excluded. Read `docs/REVH_MECHANICAL_REVIEW.md` and `docs/REVH_NPBX1_POWER.md` before using these exports.

Power JP2 is side-facing at(7.5,11.4),270deg; RP4 at(7.0,2.8). All pad nets and P_SW/P_FB track geometry are preserved. The nominal battery-side channel is7mm; strip/battery are shifted1mm right and1.4mm down. Follow docs/REVH_SIDE_POWER_PORT.md and REVH_COMPLETE_POWER_HARNESS.md. No qualified wire,screen support or holder release.

SGDCONN JH1 now uses SGDBF-08-020P-H45 (AFE F) and SGDBM-08-020P-H40 (digital B), Taobao item860586965302/PH0.8. Follow the linked SGD003/004 drawing: lands0.30x2.00mm; two finished NPTH locator holes per board require diameter0.65+0.03/-0mm at9mm span. Combined8.5mm H tolerance is not explicit on that drawing; do not inherit the old JME+/-0.15mm. Verify local assembled surface gap>=8.3mm, exact delivered mating and manufacturer hole capability. These exports remain NOT FOR ORDER.

Digital JH2 is now the right-facing TH S4B-PH-K-S. Trim/inspect its solder and tails to <=1.2mm below B; follow docs/REVH_POWER_HARNESS.md.

Front/back SMT positions are exported separately; hand-assembled through-hole connectors, probes and mounting hardware are not an SMT-only placement file. BOM lists and manufacturing stackup/impedance, thermal-via and assembly-process requirements must be reviewed before an actual fabrication release. Clean static checks do not prove assembly, functional acquisition or patient isolation.

`MANIFEST.json` binds each export to its current PCB hash. Regenerate this directory after any board change.

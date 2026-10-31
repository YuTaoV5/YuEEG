# Rev H engineering Gerber / drill / SMT export

**NOT FOR ORDER — mechanical and sourcing gates remain open.** These files are for engineering review, not a released production package. No order ZIP is generated.

AFE: 48×60mm, four copper layers. Digital: 48×60mm, six copper layers. Power strip: 34×18mm, two copper layers. Main board thickness is presently 1.6mm; the power board probe version and thickness are not yet finalized.

AFE and digital each have three 2.4mm round internal openings at (44,4), (44,51), (4,55), represented in **Edge.Cuts**. They are not duplicated as Excellon drill hits. CAM must preserve all three internal circles. M2 mounting screws, spacers and washers must be insulating.

The current power-board JP1 is still a temporary logical terminal; the verified probe reference has not been integrated. Screen FPC reach, support height, battery contact alignment/polarity and exact mating connector procurement remain unresolved. Read `docs/REVH_MECHANICAL_REVIEW.md` and `docs/REVH_NPBX1_POWER.md` before using these exports.

Digital JH2 is now the right-facing TH S4B-PH-K-S. Trim/inspect its solder and tails to <=1.2mm below B; follow docs/REVH_POWER_HARNESS.md.

Front/back SMT positions are exported separately; hand-assembled through-hole connectors, probes and mounting hardware are not an SMT-only placement file. BOM lists and manufacturing stackup/impedance, thermal-via and assembly-process requirements must be reviewed before an actual fabrication release. Clean static checks do not prove assembly, functional acquisition or patient isolation.

`MANIFEST.json` binds each export to its current PCB hash. Regenerate this directory after any board change.

# Rev D fabrication review notes

Engineering review only; obtain a board-house process review before ordering.

- Four copper layers; 84 x 122 mm; nominal 1.6 mm board. Confirm stack-up and USB trace impedance with the fabricator.
- Standard trace / clearance: 0.15 mm; local NexFET pad clearance: 0.13 mm. Minimum via: 0.5 mm copper / 0.2 mm drill.
- **72 vias intersect SMT pads. These require filled and copper-capped via-in-pad processing, not an ordinary open/tented hole.** Coordinates and associated pads: `../review/via_in_pad.json`, absolute KiCad millimetres. Review paste and assembly before fabrication.
- HOST and system copper are separated by an 8 mm rule on all layers. Preserve the L-shaped no-copper areas; do not bridge with mounting metal, shields or cables.
- THM6-0511 is the standard pin variant, not -B1 or WI. Check manufacturer top/bottom view, height and body against the custom footprint.
- The custom ADuM4160 BRIZ land pattern retains an 8.5 mm copper gap. Verify lead-to-land contact and assembly tolerance against the actual RI-16 package.
- The 3D illustration uses available library models and does not prove package fit, insulation or mechanical assembly.
- Component certifications do not certify this assembled board. USB, battery, thermal, noise, ESD, leakage and dielectric tests remain pending.

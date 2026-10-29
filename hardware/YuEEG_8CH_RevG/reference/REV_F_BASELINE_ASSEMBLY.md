# Rev F fabrication and assembly review

PCB 70 × 80 mm; four copper layers; nominal 1.6 mm. All 305 footprints are on the top face. Bottom has no SMT placement. Through-hole headers, USB shell retention and the THM6 module still require a separate solder operation where present.

Default trace/clearance 0.15 mm; local NexFET pad clearance 0.13 mm. Minimum via 0.4 mm copper / 0.2 mm drill. Confirm the proposed stack-up, USB impedance and solder-mask registration with the fabricator.

**68 vias intersect SMT pads. Review filled and copper-capped via-in-pad processing.** Coordinates: `../review/via_in_pad.json`. Tenting is not a substitute for filling/capping these holes. Use this inventory for a board-house quotation before ordering.

The dedicated Samtec FTSH-110 custom footprint follows manufacturer Rev H land dimensions; its suggested 0.152 mm stencil must be reconciled with 0402 parts using a reviewed stencil/profile. Module envelope models are illustrative. Confirm pin 1, connector mating, paste apertures and all actual component heights.

Preserve the 8 mm host/secondary copper barrier on every layer and the no-copper moat. Nonconductive mounting hardware must not bridge it. Main J301 pogo is nonisolated bench access. Unplug the entire electrode harness before charging or using nonisolated debug equipment.

AMOLED uses four nominal 8 mm insulated standoffs and a verified custom 20-to-18 harness. Confirm supplier CN1, actual mating height, cable bend radius, antenna clearance and enclosure access. Battery and enclosure are not selected; PCB dimensions do not specify the complete device volume.

Engineering review only. Actual rails, startup, USB/Wi-Fi/SD concurrency, noise, thermal behavior, pack protection, charging, leakage and dielectric performance require bench qualification before electrode use.

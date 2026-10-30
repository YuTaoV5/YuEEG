# Rev H mechanical model status

`ESP32-S3-WROOM-1U.step` is the Espressif model; its source and alignment are recorded separately. Samtec SQT/TMM models and the following files are original dimensional envelopes made from the referenced drawings, **not supplier CAD**:

- `SKRTLBE010_envelope.wrl`: 4.5 mm side switch, nominal height 3.3 mm, outward actuator; no guide bosses.
- `JST_S4B_PH_SM4_envelope.wrl`: correct SMT side-entry PH4 body, nominal height 5.5 mm; no mating plug or wire volume.
- `KINGCONN_7TFCN_FA_1010_C_envelope.wrl`: short socket, height 3.75 mm and inserted card underside at 2.56 mm; not a card insertion sweep.
- `OCN_OK_14F024_04_envelope.wrl`: female socket Rev B, maximum body height 0.87 mm. This does not solve screen FPC reach.
- `TDK_SPM4015_LR_envelope.wrl`: 4.60×4.30×1.50 mm maximum body envelope.
- `Diodes_SOT523_envelope.wrl`: maximum body and simplified lead envelope, height allowance 0.90 mm.
- `TI_DGN8_envelope.wrl`: 3.10×3.10 mm body and simplified 5.05 mm lead span, maximum height 1.10 mm.

`MillMax_0906_1_midstroke.wrl` is a manufacturer-based probe envelope at 0.70 mm compression; its footprint is a mounting reference and is not yet fitted to the power PCB. It does not prove NP-BX1 contact alignment or polarity. The power eFuse uses the installed KiCad generic WSON-8 package model with matching 2×2 mm body, 0.5 mm pitch and 0.9×1.6 mm EP; the electrical footprint remains the original Texas-named footprint.

Bounds, primary references and installed native PCB bindings are in `../review/component_envelopes.json`. These envelopes support interference review only; they do not prove tolerances, electrical insulation, procurement or assembly.

`AM178_STACK.wrl` represents the superseded 35×67 mm carrier and 10 mm standoff plan. It is **not the current stack** and must not be used to release an enclosure. Other unused inherited models (THM6, old OLED/button/card models) are also legacy references. Unresolved missing models are listed in `../review/model_audit.json`.

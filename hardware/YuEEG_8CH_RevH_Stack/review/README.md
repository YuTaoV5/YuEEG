# Current engineering evidence

Use `current_check_summary.json` to identify current PCB and schematic/project/BOM/netlist hashes. Each board's `review/drc_current.json`, `erc_current.json`, `expected_connections.json`, `pcb_pin_contract.json` and `netlist.xml` apply to the current native project. `python scripts/verify_rev_h.py` checks these bindings, native pin/BOM consistency, firmware snapshot and engineering exports; it does not rerun KiCad or approve physical hardware.

`interboard_xy_check.json` checks twenty mating pin locations and nominal insertion. `mounting_holes.json` describes the three 2.4mm Edge.Cuts openings per AFE/digital board. `component_envelopes.json` records simplified dimensional models; `model_audit.json` still lists unresolved CAD items. Screen and pogo evidence is under `mechanical/current/`.

`devtools/` preserves development transformations, including one-shot migration scripts. Some depend on local `logs/`, old source generations, KiCad Python or local tool paths. **Do not replay the directory as a clean-build pipeline.** Edit the supplied native KiCad projects and regenerate checks/exports deliberately. Current native source files are the editable design; these historical transformations are supporting evidence.

The engineering checkpoint remains incomplete: the power-board temporary terminal must be replaced by a qualified battery-probe arrangement; screen FPC reach/support and exact procurement are unresolved; size optimization and final assembly/process review remain open. No current report proves acquisition noise, full concurrent operation, assembled isolation or human-use qualification.

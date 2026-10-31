# Rev H engineering review helpers

Run from the repository root. These scripts retain development paths under `logs/`; they are checkpoint/recovery tools rather than an installation package. Scripts importing `pcbnew` require KiCad's Python, and native CLI paths reflect this workstation. Review a script before running it.

`build_*`, `route_*`, `adopt_*`, `finish_*`, `update_*` and `model_*` can mutate candidates, source boards or models. They record one-time development changes and must not be executed as a batch or used to reconstruct the current revision blindly. Candidate and baseline hashes guard specific adoption steps. `fill_h_native_board.py` refills an authoritative board and changes its source hash; all dependent evidence must then be regenerated.

Read-only native checks include `extract_h_power_ports.py`, `extract_h_host_external.py`, `check_h_afe_host_screen.py`, `audit_h_usb_geometry.py`, `audit_h_usb_reference.py` and the display-fold checks. `refresh_h_review_bundle.py` coordinates selected evidence generation but does not replace native static checks, rendering, exports or the final repository verifier. It expects the corresponding helpers under `logs/`.

`render_h_current.py` writes only disposable rendering copies and rendered evidence; it binds PCB and local model hashes. `export_h_engineering_review.py` exports review-only Gerber, drill and SMT data and checks M2 openings plus the USB mouth relief. It does not generate an order package. Final artifact binding validation is `python scripts/verify_review.py`; its success does not qualify electrical performance, assembly or patient isolation.

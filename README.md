# DentXplain

DentXplain is a research prototype for hierarchical analysis of panoramic dental
X-rays. The project will compare a flat detector with a quadrant → tooth → FDI →
diagnosis pipeline on the DENTEX benchmark.

The intended output is an auditable research result: each abnormal-tooth box is
associated with a quadrant, tooth number, FDI number, diagnosis, confidence, and
review status. It is not a diagnostic or treatment system.

## Current status

**Phase 2 — B0 diagnosis and B1 FDI tooth-enumeration baselines are complete.**
The B2 unconstrained box-matching cascade is next.

- Official source and archive sizes recorded.
- Validation annotation schema inspected.
- Validation image archive downloaded locally for integrity and visual review.
- Training archive downloaded, verified, and selectively extracted.
- The 705-image full-label pool is frozen as 564 training + 141 development
  validation images; the official 50-image cohort remains locked for final use.
- B0 YOLO labels and image hard-links are prepared without duplicating image bytes.
- The 960 px B0 run stopped at epoch 38 and selected epoch 28 on development
  mAP50-95. It reached 0.545 mAP50 and 0.368 mAP50-95 without touching the locked
  50-image final cohort.
- The B1 pool excludes all 18 enumeration images that exactly overlap the final
  cohort. Its SHA-grouped split contains 492 training and 124 development-validation
  images with all 32 permanent-tooth FDI classes represented.
- The selected B1 checkpoint reached 0.951 mAP50 and 0.545 mAP50-95 across all
  32 FDI classes on development validation.
- A 100-image joint development cohort unseen by both model training sets is
  frozen for B2 matching and abstention thresholds.

## Dataset boundary

DENTEX data is not part of this repository. The current Hugging Face dataset card
labels it `CC BY-NC-SA 4.0`; therefore data and derived data are handled as
non-commercial research material and kept outside Git. The repository code is
planned to use the MIT license independently.

## Planned experiment

1. Establish a simple fully-annotated flat detector baseline.
2. Add quadrant and enumeration supervision without treating missing diagnosis
   labels as negatives.
3. Apply FDI sequence and neighborhood consistency constraints.
4. Compare the same frozen split using AP/AR, FDI accuracy, class-wise recall,
   calibration, and risk–coverage.

## First commands

```powershell
python -m pip install -e ".[dev,audit]"
python scripts/audit_validation.py `
  --annotations data/raw/metadata/validation_triple.json `
  --images data/raw/validation_data/validation_data/quadrant_enumeration_disease/xrays `
  --output artifacts/data_audit/validation_audit.json
python -m pytest -q
python scripts/train_b0.py `
  --data data/processed/b0_yolo/dentex_b0.yaml `
  --epochs 1 --image-size 640 --batch 1 --name b0_smoke_640

python scripts/train_b0.py `
  --data data/processed/b0_yolo/dentex_b0.yaml `
  --epochs 40 --image-size 960 --batch 2 --name b0_main_960

python scripts/train_b1.py `
  --data data/processed/b1_yolo/dentex_b1.yaml `
  --epochs 40 --image-size 960 --batch 2 --name b1_main_960
```

See [the data-gate record](docs/data_gate.md) for confirmed facts and risks, and
[the experiment contract](docs/experiment_contract_v1.md) for the leakage-safe
evaluation boundary and ordered model ladder. The complete B0 interpretation is
recorded in [the B0 result report](docs/b0_results.md), and the FDI baseline in
[the B1 result report](docs/b1_results.md).

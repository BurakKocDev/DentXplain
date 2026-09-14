# DentXplain

DentXplain is a research prototype for hierarchical analysis of panoramic dental
X-rays. The project will compare a flat detector with a quadrant → tooth → FDI →
diagnosis pipeline on the DENTEX benchmark.

The intended output is an auditable research result: each abnormal-tooth box is
associated with a quadrant, tooth number, FDI number, diagnosis, confidence, and
review status. It is not a diagnostic or treatment system.

## Current status

**Phase 4 — the locked B0/B1/B2/C1 evaluation is complete.** C1 retained its
development advantage on the official 50-image cohort; packaging and demo work
remain.

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
- On that cohort, B2 reached 0.502 joint F1 and C1 reached 0.510 while increasing
  correct diagnosis+FDI results from 313 to 320. The official final cohort remains
  untouched.
- Thresholded B0 error analysis confirms Periapical Lesion recall (0.259) and
  Caries false positives (290) as the priorities for the next controlled ablation.
- B0-R1 whole-image rare-class resampling was tested and rejected: AP50-95 fell
  from 0.369 to 0.355 and Periapical Lesion did not improve. The original B0
  checkpoint remains selected.
- B0-R2 changed only global input resolution from 960 to 1280 px and was also
  rejected: AP50-95 reached 0.360 and Periapical Lesion fell to 0.181. Further
  development tuning is stopped; the selected B0+B1+C1 bundle is ready to freeze.
- The pre-frozen C1 configuration reached 0.372 joint precision, 0.610 recall,
  0.463 F1, and 0.957 conditional FDI accuracy on the official 50-image final
  cohort. C1 reduced wrong FDI assignments from eight to five relative to B2.
- Ten-thousand-image-level bootstrap resamples place C1 F1 at 0.385–0.534; the
  paired C1−B2 interval includes zero, so superiority is not claimed.

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
[the B1 result report](docs/b1_results.md). Joint cascade results are in
[the B2/C1 report](docs/b2_c1_results.md), with the bottleneck analysis in
[the B0 error report](docs/b0_error_analysis.md) and the rejected sampling
experiment in [the B0-R1 report](docs/b0_r1_results.md). The resolution ablation
is recorded in [the B0-R2 report](docs/b0_r2_results.md).
The locked outcome and uncertainty analysis are in
[the final result report](docs/final_results.md); intended use and limitations are
summarized in [the model card](MODEL_CARD.md).

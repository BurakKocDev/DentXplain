# DentXplain

DentXplain is a research prototype for hierarchical analysis of panoramic dental
X-rays. The project will compare a flat detector with a quadrant → tooth → FDI →
diagnosis pipeline on the DENTEX benchmark.

The intended output is an auditable research result: each abnormal-tooth box is
associated with a quadrant, tooth number, FDI number, diagnosis, confidence, and
review status. It is not a diagnostic or treatment system.

## Current status

**Phase 0 — data and license gate is in progress.** No model training has started.

- Official source and archive sizes recorded.
- Validation annotation schema inspected.
- Validation image archive downloaded locally for integrity and visual review.
- Full 10.9 GB training archive intentionally deferred until the gate passes.

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
```

See [the data-gate record](docs/data_gate.md) for confirmed facts, risks, and the
decision required before the full dataset download.


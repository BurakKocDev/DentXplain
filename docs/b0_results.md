# B0 diagnosis detector — development result

Status: **complete; suitable as the flat diagnosis baseline for B1/B2 comparison.**

## Run boundary

- Model: YOLOv8s initialized from `yolov8s.pt`
- Development split: 564 training and 141 calibration-validation panoramics
- Input: 960 px; batch size 2; AMP; deterministic seed `20260913`
- Augmentation: no mosaic, mixup, or copy-paste; mild translation, scale, horizontal
  flip, and intensity variation
- Selection: maximum development-validation mAP50-95
- Early stopping: epoch 38 after ten epochs without improvement
- Selected checkpoint: epoch 28
- Selected weight SHA-256:
  `cab3d3e5aafb960e9ddef8a6c38c6999082fdfea69f5008826fa47a94404c87f`
- The official 50-image final cohort was not loaded or evaluated.

## Development-validation result

| Class | Images | Boxes | Precision | Recall | AP50 | AP50-95 |
|---|---:|---:|---:|---:|---:|---:|
| All | 141 | 743 | 0.502 | 0.603 | 0.545 | 0.369 |
| Impacted Tooth | 51 | 115 | 0.780 | 0.922 | 0.885 | 0.600 |
| Caries | 125 | 466 | 0.421 | 0.631 | 0.502 | 0.371 |
| Periapical Lesion | 22 | 33 | 0.388 | 0.303 | 0.306 | 0.195 |
| Deep Caries | 65 | 129 | 0.419 | 0.558 | 0.489 | 0.309 |

These are development metrics, not a final generalization claim. Thresholds and
calibration may use this split; the frozen final cohort remains reserved for the
pre-registered B0/B2/C1 comparison.

## Interpretation

The detector has learned a meaningful baseline rather than merely completing the
pipeline. Impacted teeth are the easiest target because their shape and position
are distinctive. Ordinary and deep caries are moderately localized but frequently
confused with one another. Periapical lesions are the clear bottleneck: only 33
development-validation boxes are available and most misses are assigned to
background.

The normalized confusion matrix and visual samples support the same conclusion:

- impacted-tooth boxes are usually well localized;
- caries predictions generally land on plausible tooth regions;
- Caries and Deep Caries sometimes produce overlapping or swapped predictions;
- small/subtle periapical findings are often missed;
- validation loss bottoms before the end while training loss keeps falling, so
  selecting epoch 28 instead of the final epoch is justified.

## Decision

B0 passes the project gate: it runs end-to-end, reports all four diagnosis classes,
and establishes a non-trivial flat baseline. The next experiment is B1, a separate
32-class FDI tooth detector. B1 must exclude the 18 enumeration images that exactly
overlap the locked final cohort and keep each internal exact-duplicate group on one
side of its development split. Horizontal flips must be disabled for B1 unless FDI
quadrants are remapped.

After B1, B2 will match B0 pathology boxes to B1 tooth boxes. Only then should we
test anatomy-constrained sequence reasoning (C1). Class rebalancing or targeted
periapical improvements remain a later B0 ablation, not a reason to change the
frozen baseline retrospectively.

# B1 FDI tooth detector — development result

Status: **complete; accepted as the anatomical detector for the B2 cascade.**

## Run boundary

- Model: YOLOv8s initialized from `yolov8s.pt`
- Eligible pool: 616 panoramics after removing 18 exact overlaps with the locked
  final cohort
- Development split: 492 training and 124 calibration-validation panoramics,
  grouped by encoded-image SHA-256
- Labels: 32 permanent-tooth FDI classes; 13,878 training and 3,702 validation boxes
- Input: 960 px; batch size 2; AMP; deterministic seed `20260913`
- Horizontal flip: disabled to preserve FDI left/right quadrant semantics
- Selection: maximum development-validation mAP50-95
- Early stopping: epoch 16 after ten epochs without improvement
- Selected checkpoint: epoch 6
- Selected weight SHA-256:
  `0f6faf5b200b8b02ce47a33433dcae1155b02af0c1774a481c199ccbfa68113d`
- Split-manifest SHA-256:
  `02f84e0c85455c9e1db570b1cdb9533808da024ffa816ab4d871a6b8084be0fb`
- The official 50-image final cohort was not evaluated.

## Development-validation result

| Scope | Precision | Recall | AP50 | AP50-95 |
|---|---:|---:|---:|---:|
| All 32 FDI classes | 0.911 | 0.930 | 0.951 | 0.545 |

The weakest AP50 class is FDI 14 at 0.868; most classes lie between 0.92 and
0.99 AP50. At stricter localization thresholds, FDI 14 is also weakest at 0.416
AP50-95. FDI 36, 47, and 46 are strongest at 0.621, 0.612, and 0.607 AP50-95.
Every class is represented and evaluated.

## Interpretation

FDI enumeration is substantially easier than four-way pathology localization in
this dataset because tooth position follows a stable anatomical sequence. The
normalized confusion matrix is strongly diagonal. Most residual class errors are
between adjacent tooth positions rather than distant quadrants.

Visual validation shows that predicted boxes track both dental arches and usually
retain the correct order. Errors concentrate around absent teeth, the terminal
molars, overlapping structures, and small box-boundary shifts. The gap between
0.951 AP50 and 0.545 AP50-95 means class identity is strong while tight box geometry
still has room to improve. Validation box/DFL loss bottoms near the selected epoch
and then rises while training loss keeps falling, supporting early checkpoint
selection.

These are development metrics, not final generalization claims. The final cohort
remains locked until the same B0/B2/C1 comparison can be run once.

## Decision

B1 passes its gate and becomes the fixed anatomical detector for B2. The next step
is to run B0 and B1 on a common development image set, then match each B0 pathology
box to at most one B1 tooth box using IoU plus normalized center distance. B2 may
abstain when no tooth clears a development-derived threshold. C1 will later apply
FDI order and one-to-one constraints to the same detector outputs so the value of
anatomical reasoning is measured without retraining either detector.

The common development audit found 41 B0 validation images that B1 had seen under
different names during training. They are excluded from combined evaluation. The
resulting 100-image joint cohort is exact-image clean against both training sets
and is the only cohort permitted for B2/C1 threshold development.

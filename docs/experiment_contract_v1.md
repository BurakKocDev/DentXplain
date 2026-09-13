# DentXplain experiment contract v1

Status: **frozen for data preparation; model training remains gated.**

## Primary question

Does explicit tooth enumeration plus FDI sequence consistency improve joint
localization–enumeration–diagnosis reliability over a diagnosis-only detector and
an unconstrained cascade?

## Frozen evaluation boundary

- The 50-image `validation_triple.json` cohort is the locked final evaluation set.
  It is not used for fitting, early stopping, threshold selection, or calibration.
- The 705 fully annotated training images form the development pool. A deterministic
  duplicate-aware split will be frozen only after image hashes are available.
- Target development ratio is approximately 80/20 train/calibration-validation,
  stratified by diagnosis presence and grouped by exact/near-duplicate identity.
- The public 250-image test archive is secondary/exploratory because its LabelMe
  ontology does not directly match the four-class COCO training schema. It cannot
  affect the primary result until an owner-supported mapping is documented.
- No patient-level claim will be made because no patient identifier has been
  confirmed.

## Data inclusion matrix

| Dataset level | Images | Valid supervision | Forbidden interpretation |
|---|---:|---|---|
| Quadrant only | 693 | Four quadrant boxes/classes | Missing tooth/diagnosis = negative |
| Quadrant + enumeration | 634 | Tooth boxes, quadrant, position/FDI | Missing diagnosis = negative |
| Full train | 705 | Abnormal-tooth boxes, quadrant, tooth, diagnosis | Zero boxes = clinically healthy |
| Full validation | 50 | Same four-class hierarchy; final test only | Hyperparameter tuning |
| Unlabeled | 1,571 | Optional self-supervised pretraining only | Pseudo-labels as ground truth |

## Ordered model ladder

### B0 — diagnosis detector

- YOLOv8s, four diagnosis classes, trained only on the 705-image full development
  pool after its split is frozen.
- A 640 px one-epoch smoke run precedes a 960/1,024 px rectangular main run using
  automatic mixed precision, batch size 1, and gradient accumulation on 4 GiB VRAM.
- Purpose: establish localization and diagnosis difficulty with minimal engineering.

### B1 — FDI tooth detector

- Thirty-two permanent-tooth FDI classes learned from the 634-image
  quadrant+enumeration subset.
- Missing/unerupted teeth are not synthesized as positive or negative boxes.
- Purpose: produce an anatomical tooth map independent of pathology labels.

### B2 — unconstrained cascade

- Match B0 abnormal-tooth boxes to B1 tooth boxes by overlap and center distance.
- Emit diagnosis + FDI only when a match clears a development-derived threshold;
  otherwise abstain from enumeration.
- Purpose: fair baseline for anatomical post-processing.

### C1 — anatomy-constrained DentXplain

- Enforce left/right quadrant orientation, monotonic tooth order, plausible
  adjacency, and one-to-one assignment with a sequence/graph optimizer.
- Do not move or invent a diagnosis box solely to satisfy anatomy.
- Compare with B2 using identical detector outputs; this isolates the contribution
  of anatomical reasoning.

### C2 — multi-head candidate

- Optional shared RoI representation with class-agnostic box regression and
  separate quadrant, position, and diagnosis heads.
- Starts only if B0–C1 establish a reproducible benchmark and compute remains.

## Primary metrics

- COCO AP, AP50, AP75 and AR separately for quadrant, enumeration, and diagnosis.
- Joint AP where a true positive requires IoU ≥ 0.50 plus correct quadrant,
  tooth position, and diagnosis.
- FDI accuracy and Macro F1 on correctly localized/matched teeth.
- Diagnosis sensitivity per class, with special reporting for Periapical Lesion.
- Class-wise ECE, Brier score, reliability curves, and risk–coverage.
- Bootstrap 95% confidence intervals at image level for final comparisons.

## Pre-registered slices

- Diagnosis class and FDI position
- Images with metal restorations/implants
- Low contrast/blur and black-border/cropping variation
- Zero-target-annotation images
- Single versus multiple abnormal-tooth images
- Anterior (positions 1–3) versus posterior (positions 6–8) teeth

## Stop/go gates

Training may start only when:

1. the 705 training images are present and match the annotation manifest;
2. corrupt, exact duplicate, and near-duplicate audits are complete;
3. the development split manifest and its SHA-256 are frozen;
4. a one-batch loader/augmentation visualization passes;
5. disk and GPU budgets are recorded.

The project advances from B0 to B1 only if B0 runs end-to-end and reports all four
classes without using the locked 50-image evaluation cohort for selection.

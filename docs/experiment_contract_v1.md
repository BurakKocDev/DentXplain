# DentXplain experiment contract v1

Status: **frozen; B0–C1 development ladder complete, final evaluation still locked.**

## Primary question

Does explicit tooth enumeration plus FDI sequence consistency improve joint
localization–enumeration–diagnosis reliability over a diagnosis-only detector and
an unconstrained cascade?

## Frozen evaluation boundary

- The 50-image `validation_triple.json` cohort is the locked final evaluation set.
  It is not used for fitting, early stopping, threshold selection, or calibration.
- The 705 fully annotated training images form the development pool. The frozen
  split contains 564 training and 141 calibration-validation images, stratified
  by multi-label diagnosis-presence signature with seed `20260913`.
- The local split manifest SHA-256 is
  `eccefd126f454dedb2dfcca3992820fbc01a1db290f85d7d440bbefdb8d40462`.
  The full-label pool has no internal exact duplicate and no exact overlap with
  the locked final cohort.
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
- A 640 px one-epoch smoke run precedes a shuffled 960 px main run using automatic
  mixed precision and batch size 2 on 4 GiB VRAM.
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
- Tune matching and abstention only on the frozen joint development cohort that
  is unseen by both B0 and B1; do not use either model's full independent
  validation split for the combined score.
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

For B1, 18 enumeration images that are byte-identical to locked-final images are
excluded before fitting. The nine internal exact-duplicate groups in the remaining
enumeration pool must be grouped on a single side of its development split.

The frozen B1 manifest satisfies this rule: 616 eligible images are divided into
492 training and 124 calibration-validation images, containing 13,878 and 3,702
tooth boxes respectively. All 32 FDI classes occur on both sides. Its manifest
SHA-256 is
`02f84e0c85455c9e1db570b1cdb9533808da024ffa816ab4d871a6b8084be0fb`.

## B0 smoke record

The 640 px, one-epoch smoke run completed on the RTX 3050 Ti with CUDA 12.6. It
processed 564 training and 141 calibration-validation images, reported all four
classes, produced loader/label visualizations, and used less than 0.5 GiB reported
GPU memory. Its mAP50 of approximately 0.02 is a pipeline check, not a performance
claim or a selected checkpoint. Visual review found the transformed boxes aligned
with the intended panoramic regions.

The main B0 run uses 960 px, batch size 2, AMP, 40 maximum epochs, early stopping,
and no mosaic/mixup/copy-paste. Square shuffled batches are preferred over
Ultralytics rectangular mode because that mode disabled shuffling in the smoke
run. The locked 50-image cohort remains untouched.

## B0 main record

The main run stopped at epoch 38 after ten epochs without development improvement
and selected epoch 28. On the 141-image calibration-validation split it reached
0.502 precision, 0.603 recall, 0.545 mAP50, and 0.368 mAP50-95. Impacted Tooth was
strongest at 0.600 AP50-95; Periapical Lesion was weakest at 0.195. The locked
50-image cohort remained untouched. See `docs/b0_results.md` for the complete
class-wise result and interpretation.

## B1 smoke record

The 640 px, one-epoch B1 smoke run completed on the same GPU with all 492 training
and 124 calibration-validation images. It loaded 32 FDI classes and 17,580 boxes
without corrupt images, backgrounds, or duplicate source labels. Visual review
confirmed that boxes follow the upper/lower tooth rows and the YAML loader maps
class IDs 0–31 to FDI 11–48 correctly. Horizontal flipping is disabled because it
would invalidate left/right FDI quadrants. The near-zero one-epoch AP is only a
pipeline check and is not a selected model result.

## B1 main record

The B1 main run stopped at epoch 16 and selected epoch 6. Across 32 FDI classes on
the 124-image development-validation split it reached 0.911 precision, 0.930
recall, 0.951 mAP50, and 0.545 mAP50-95. The confusion matrix was strongly
diagonal; visual errors concentrated around adjacent positions and terminal
molars. The locked final cohort remained untouched. See `docs/b1_results.md` for
the complete interpretation and checkpoint identity.

## Joint B2/C1 development boundary

The independently valid B0 and B1 splits cannot be combined naively: 41 of the
141 B0 calibration-validation images are exact encoded-image matches to B1
training images under different file names. Those images remain valid for B0-only
evaluation but are excluded from every combined B2/C1 development score.

The frozen joint cohort contains the remaining 100 B0 calibration-validation
images and has no exact overlap with either model's training examples. Fifteen of
the 100 are also in B1 calibration-validation, which is allowed because B1 did not
fit them. The joint manifest SHA-256 is
`f0f0844afe32bf739b317ebecf5fad7e625371edfe7addb03031ffba5db66491`.
The locked 50-image final cohort remains untouched.

## B2/C1 development record

B0 and B1 predictions were cached once for the frozen 100-image joint cohort, so
B2 and C1 use identical detector outputs. A 525-configuration development grid
selected thresholds by maximum joint F1. B2 reached 0.443 precision, 0.580 recall,
and 0.502 joint F1 with 0.918 conditional FDI accuracy. C1's monotonic upper/lower
arch sequence reached 0.448 precision, 0.593 recall, and 0.510 joint F1 with 0.917
conditional FDI accuracy. Correct diagnosis+FDI assignments increased from 313 to
320 of 540 targets. C1 is therefore selected for the final comparison; see
`docs/b2_c1_results.md`.

At C1's selected B0 confidence threshold, the clean joint cohort contains 353
class-correct IoU50 detections, 371 false positives, and 187 false negatives.
Periapical Lesion recall is 0.259, while Caries contributes 290 false positives.
The next permitted experiment is a frozen-baseline B0 improvement ablation; it may
not use the official 50-image final cohort for model or threshold selection.

## B0-R1 ablation record

The first B0 improvement candidate repeated rare-class training images once while
holding the validation split and all other training settings fixed. It stopped at
epoch 28 and selected epoch 18. AP50-95 fell from 0.369 to 0.355; Periapical
Lesion remained effectively unchanged at 0.194, while Caries fell from 0.371 to
0.306. B0-R1 is rejected and cannot replace the selected B0 checkpoint. See
`docs/b0_r1_results.md`. A subsequent resolution ablation may use the original
sampling only and must remain development-only.

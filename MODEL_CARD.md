# DentXplain model card

## Model summary

DentXplain combines two YOLOv8s detectors and deterministic anatomical
post-processing for panoramic dental X-rays:

1. B0 localizes four abnormality classes: Impacted, Caries, Periapical Lesion,
   and Deep Caries.
2. B1 detects 32 permanent-tooth FDI positions.
3. C1 retains maximum-confidence monotonic upper/lower FDI sequences and assigns
   B0 boxes to tooth boxes using frozen overlap/center-distance thresholds.

This is a research prototype, not a medical device.

## Intended use

- Reproducing hierarchical object-detection experiments on DENTEX
- Studying whether anatomical constraints reduce tooth-enumeration errors
- Demonstrating leakage-aware data splitting, abstention, error analysis, and
  paired uncertainty estimates
- Expert-supervised research demos

## Out-of-scope use

- Diagnosis, treatment selection, triage, or autonomous clinical decisions
- Screening populations or replacing dental professionals
- Use on intraoral photographs, CBCT, pediatric dentition, or non-panoramic images
- Commercial use of DENTEX-derived artifacts without separately resolving the
  dataset's license and permissions

## Data and evaluation

DENTEX data is handled locally and excluded from Git. The working dataset license
is CC BY-NC-SA 4.0. B0 used 564 training and 141 development-validation images.
B1 used 492 training and 124 development-validation images after excluding 18
exact overlaps with the locked final cohort. Combined thresholds used a separate
100-image exact-image-clean joint development cohort. The official 50-image,
182-target cohort was evaluated once after configuration freeze.

## Final performance

At the frozen C1 operating point, joint precision is 0.372, recall 0.610, and F1
0.463. A joint true positive requires class-correct IoU >= 0.50 and correct FDI.
Conditional FDI accuracy on emitted, correctly localized pathology is 0.957.
The 95% image-bootstrap interval for C1 joint F1 is 0.385–0.534. The paired C1−B2
F1 interval is -0.019–0.032, so statistical superiority is not established.

## Limitations

- The final cohort contains only 50 images and nine Periapical Lesion targets.
- B0 produces many Caries false positives and confuses Caries with Deep Caries.
- Patient identifiers and institution/protocol metadata are unavailable, so no
  patient-level or external-domain generalization claim is possible.
- FDI performance is conditional on successful pathology localization and cannot
  compensate for a missed lesion.
- Calibration, OOD detection, clinical reader studies, and prospective validation
  are not complete.

## Reproducibility

The frozen configuration is `configs/evaluation/dentex_final_v1.json`. Model
hashes, thresholds, data boundaries, ablations, and final results are documented
in `docs/experiment_contract_v1.md` and `docs/final_results.md`. Generated model
weights, predictions, and DENTEX data remain outside Git.

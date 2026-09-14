# B2/C1 cascade — joint development result

Status: **complete on development; C1 selected for the locked final comparison.**

## Evaluation boundary

- Cohort: 100 panoramics and 540 abnormal-tooth targets unseen by both B0 and B1
  training sets
- Cohort-manifest SHA-256:
  `f0f0844afe32bf739b317ebecf5fad7e625371edfe7addb03031ffba5db66491`
- Detector outputs are identical for B2 and C1; only FDI post-processing changes.
- Grid: 525 configurations over B0 confidence, B1 confidence, IoU/center weighting,
  and match/abstention threshold
- Selection: maximum joint F1; ties resolved by precision and then recall
- Joint correctness requires a diagnosis box with class-correct IoU >= 0.50 and the
  correct FDI assignment.
- The official 50-image final cohort remains untouched.

## Maximum-F1 operating point

| Method | B0 conf. | B1 conf. | IoU weight | Match threshold | Precision | Recall | F1 | Correct / 540 | FDI accuracy on localized pathology | Assignment coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B2 unconstrained | 0.20 | 0.25 | 1.00 | 0.60 | 0.443 | 0.580 | 0.502 | 313 | 0.918 | 0.966 |
| C1 monotonic anatomy | 0.20 | 0.10 | 0.25 | 0.70 | **0.448** | **0.593** | **0.510** | **320** | 0.917 | **0.989** |

C1 raises joint F1 by 0.008 absolute, adds seven correct diagnosis+FDI results,
and reduces unassigned B0 candidates from 18 to 9. FDI accuracy conditional on a
correctly localized pathology is effectively unchanged. The gain therefore comes
mainly from retaining a more complete, anatomically coherent tooth sequence, not
from correcting a large number of tooth identities.

## Cautious operating point

For an operating point constrained to at least 0.40 joint recall, both methods
select B0 confidence 0.30, B1 confidence 0.50, IoU-only matching, and a 0.60 match
threshold.

| Method | Precision | Recall | F1 | FDI accuracy | Emitted | Abstained |
|---|---:|---:|---:|---:|---:|---:|
| B2 unconstrained | 0.519 | 0.428 | 0.469 | 0.943 | 445 | 71 |
| C1 monotonic anatomy | **0.521** | 0.428 | **0.470** | **0.951** | 443 | 73 |

This point is preferable for a review-oriented demonstration because it removes
more weak candidates and improves conditional FDI accuracy, but it is not the
pre-registered maximum-F1 selection.

## Interpretation and decision

C1 is selected as the DentXplain development method. It applies a
maximum-confidence monotonic FDI sequence independently to the upper and lower
arches, with one retained candidate per ordered FDI position. It does not move or
invent pathology boxes.

The improvement over B2 is real but modest. B1 tooth identity is already strong;
the dominant limitation is B0 pathology detection. At the selected C1 point B0
produces 724 boxes for 540 targets, of which only 353 are class-correct IoU>=0.50
matches. Future work should prioritize B0 false-positive control, Caries/Deep
Caries separation, and Periapical Lesion recall rather than adding a more complex
FDI graph optimizer immediately.

All numbers here are threshold-development results. They are not clinical claims
and must not be presented as final generalization performance.

# DentXplain locked final evaluation

Status: **complete. No final-set model or threshold tuning was performed.**

## Frozen boundary

- Official DENTEX validation cohort: 50 panoramics, 182 abnormal-tooth targets
- Final manifest SHA-256:
  `f1fda381280817750b882c4e6a3df68bbb4a1afc6a58f80b311de457a10e9f5e`
- B0 checkpoint SHA-256:
  `cab3d3e5aafb960e9ddef8a6c38c6999082fdfea69f5008826fa47a94404c87f`
- B1 checkpoint SHA-256:
  `0f6faf5b200b8b02ce47a33433dcae1155b02af0c1774a481c199ccbfa68113d`
- Models and thresholds were committed in `9c87e8c` before final inference.
- B2 fixed thresholds: B0 0.20, B1 0.25, IoU weight 1.00, match 0.60.
- C1 fixed thresholds: B0 0.20, B1 0.10, IoU weight 0.25, match 0.70,
  monotonic upper/lower FDI sequence enabled.

## Primary final result

| Method | Joint precision | Joint recall | Joint F1 | Correct / 182 | Conditional FDI accuracy | Wrong FDI |
|---|---:|---:|---:|---:|---:|---:|
| B2 unconstrained | 0.368 | 0.599 | 0.456 | 109 | 0.932 | 8 |
| C1 anatomy-constrained | **0.372** | **0.610** | **0.463** | **111** | **0.957** | **5** |

C1 preserves the direction observed during development. It adds two correct joint
diagnosis+FDI results, raises conditional FDI accuracy by 0.025, and reduces wrong
FDI assignments from eight to five. The absolute joint-F1 increase is 0.006.

## Diagnosis slices

| Diagnosis | Targets | B2 P / R / F1 | C1 P / R / F1 | C1 correct |
|---|---:|---:|---:|---:|
| Impacted | 40 | 0.78 / 0.88 / 0.82 | 0.78 / 0.88 / 0.82 | 35 |
| Caries | 101 | 0.28 / 0.55 / 0.37 | 0.29 / 0.56 / 0.38 | 57 |
| Periapical Lesion | 9 | 0.33 / 0.33 / 0.33 | 0.30 / 0.33 / 0.32 | 3 |
| Deep Caries | 32 | 0.37 / 0.47 / 0.41 | 0.36 / 0.50 / 0.42 | 16 |

Impacted Tooth is reliable relative to the other diagnoses. Caries dominates the
false-positive burden, and only three of nine Periapical Lesion targets become
correct joint outputs. The small periapical denominator makes its estimate highly
uncertain.

## Image-level bootstrap uncertainty

Ten thousand paired bootstrap resamples use the image as the sampling unit and a
fixed seed of `20260915`.

| Metric | B2 point (95% CI) | C1 point (95% CI) | C1−B2 95% CI |
|---|---:|---:|---:|
| Joint precision | 0.368 (0.301–0.438) | 0.372 (0.303–0.443) | -0.017–0.025 |
| Joint recall | 0.599 (0.494–0.695) | 0.610 (0.506–0.703) | -0.024–0.046 |
| Joint F1 | 0.456 (0.380–0.527) | 0.463 (0.385–0.534) | -0.019–0.032 |
| Conditional FDI accuracy | 0.932 (0.870–0.977) | 0.957 (0.902–0.992) | -0.028–0.076 |

Every paired difference interval includes zero. The data therefore support a
small, directionally consistent C1 improvement, but not a claim of statistical
superiority on this 50-image cohort.

## B0 final error boundary

At the frozen 0.20 threshold, B0 has 118 class-correct IoU50 detections, 184 false
positives, and 64 false negatives: precision 0.391, recall 0.648, and F1 0.488.
Compared with joint development, recall is stable while precision falls from
0.488 to 0.391. Caries contributes 140 of 184 false positives. Likely localized
class swaps include eight Deep Caries → Caries and five Caries → Deep Caries.

## Conclusion

DentXplain demonstrates a reproducible, leakage-audited hierarchical dental
vision pipeline. The strongest result is accurate FDI assignment after successful
pathology localization; the principal bottleneck is pathology detection rather
than anatomy. C1 is retained as the final research method because it improves all
primary point estimates and reduces FDI mistakes, with the explicit limitation
that the paired uncertainty interval includes no effect.

These results are for research and software demonstration only. They do not
establish safety, clinical utility, or generalization to other institutions.

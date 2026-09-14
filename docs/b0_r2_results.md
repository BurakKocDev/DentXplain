# B0-R2 1280 px resolution ablation

Status: **complete and rejected. The original 960 px B0 checkpoint remains selected.**

## Controlled change

B0-R2 uses the original 564-image training and 141-image development-validation
split. Relative to B0, only input resolution changes from 960 to 1280 px. Model,
initialization, sampling, augmentation, batch size, seed, optimizer selection, and
maximum epoch count remain unchanged. The RTX 3050 Ti smoke test passed at batch
size 2 with approximately 1.84 GiB reported GPU memory.

The main run completed all 40 epochs and selected epoch 31. The selected weight
SHA-256 is
`a0d86bf5aa6f959aa55ea74e3dd531ff97ab4948f854321698083c278f3af163`.

## Development result

| Scope | B0 AP50-95 | B0-R2 AP50-95 | Difference |
|---|---:|---:|---:|
| All | **0.369** | 0.360 | -0.009 |
| Impacted | **0.600** | 0.596 | -0.004 |
| Caries | **0.371** | 0.368 | -0.003 |
| Periapical Lesion | **0.195** | 0.181 | -0.014 |
| Deep Caries | **0.309** | 0.295 | -0.014 |

Overall B0-R2 precision is 0.549, recall 0.573, AP50 0.541, and AP50-95 0.360.
Compared with B0, precision rises but recall and both AP metrics decline. The
smallest/rarest target, Periapical Lesion, does not benefit from the additional
pixels: its AP50-95 falls to 0.181 and recall to 0.192.

## Decision

Reject B0-R2. Neither whole-image rare-class repetition nor higher global input
resolution improves the pre-registered development metric. The original B0
epoch-28 checkpoint and C1 post-processing thresholds remain selected. Further
development-driven trial-and-error is stopped here to limit overfitting to the
development split. The next step is to freeze the B0+B1+C1 bundle and run the
official 50-image final evaluation exactly once, without retuning.

# B0-R1 rare-class resampling ablation

Status: **complete and rejected. The original B0 checkpoint remains selected.**

## Controlled change

B0-R1 changes only the training sampling distribution. The model, initialization,
564-image source training split, 141-image development-validation split, 960 px
input, augmentation, optimizer selection, batch size, seed, and early-stopping
rule remain the same as B0.

Each training image containing Periapical Lesion receives one additional sample.
Among the remaining images, one additional sample is created when Deep Caries
boxes outnumber Caries boxes. This produces 691 effective training samples from
564 unique images:

| Class | B0 effective boxes | B0-R1 effective boxes |
|---|---:|---:|
| Impacted | 489 | 602 |
| Caries | 1,722 | 2,091 |
| Periapical Lesion | 125 | 250 |
| Deep Caries | 449 | 652 |

The validation distribution is unchanged. Hard-linked aliases avoid additional
image storage and never cross the frozen split boundary.

## Development result

B0-R1 stopped at epoch 28 after ten epochs without improvement and selected epoch
18. The selected weight SHA-256 is
`1f33a39e21184f6e2bb037f6f22267f9bf23423aab2959850cecfbf70d80d85a`.

| Scope | B0 AP50-95 | B0-R1 AP50-95 | Difference |
|---|---:|---:|---:|
| All | **0.369** | 0.355 | -0.014 |
| Impacted | 0.600 | **0.613** | +0.013 |
| Caries | **0.371** | 0.306 | -0.065 |
| Periapical Lesion | **0.195** | 0.194 | -0.001 |
| Deep Caries | **0.309** | 0.305 | -0.004 |

Overall B0-R1 precision is 0.523, recall 0.560, AP50 0.533, and AP50-95 0.355.
Periapical Lesion precision is 0.347 and recall remains 0.303; doubling its
effective training-box exposure did not improve the weak-class result. Caries
recall falls from 0.631 to 0.485, producing the largest regression.

## Decision

Reject B0-R1 and retain the original B0 epoch-28 checkpoint. The result rules out
simple whole-image repetition as an effective answer to rare, small findings:
repetition also duplicates common co-occurring labels and reduces useful sample
diversity per epoch.

The next clean ablation should target spatial resolution rather than class
frequency. B0-R2 will keep the original sampling distribution and change only the
input from 960 to 1280 px, subject to a GPU smoke test. The locked 50-image final
cohort remains untouched.

# DENTEX data gate

Status: **provisionally open for metadata and validation audit; full training
download is deferred.**

## Confirmed on 2026-09-13

- The official Hugging Face repository reports a total size of 11.8 GB.
- The repository contains `training_data.zip` (10.9 GB), `test_data.zip`
  (765 MB), `validation_data.zip` (150 MB), and `validation_triple.json`
  (64.4 KB).
- The Dataset Viewer cannot load the repository because its splits mix image-folder
  and JSON formats. Local archive/schema validation is therefore required.
- The benchmark contains 693 quadrant-only, 634 quadrant+enumeration, 1,005 fully
  annotated, and 1,571 unlabeled panoramic X-rays.
- The fully annotated benchmark split is 705 train / 50 validation / 250 test.
- The validation annotation file contains 50 images and 182 abnormal-tooth
  annotations.
- Each annotation shares one box across three labels: quadrant (`category_id_1`),
  tooth position (`category_id_2`), and diagnosis (`category_id_3`).
- Diagnosis IDs map to Impacted, Caries, Periapical Lesion, and Deep Caries.

## Validation audit result

- `validation_data.zip`: 149,512,256 bytes; SHA-256
  `6370bb4f1024bd610cde13242a465cb2eff195fc02f56ac22126555e7edc7bc3`.
- `validation_triple.json`: SHA-256
  `d058afd35d2849923c7c045e61fd3e05d231dcf74d55009993fff88bd9b6f5a2`.
- All 50 referenced images are present and decodable; annotation dimensions match
  the image dimensions.
- All 182 boxes have positive area, are within image bounds, and include polygon
  segmentations. No orphan or duplicate IDs were found.
- No exact duplicate image was found among the 50 referenced files.
- Four images have zero target annotations. They are recorded as “no target
  annotation,” not assumed clinically normal.
- Diagnosis counts are Caries 101, Impacted 40, Deep Caries 32, and Periapical
  Lesion 9. The last class requires class-wise reporting and imbalance controls.
- The ZIP also contains one `.ipynb_checkpoints` image copy. Audit code excludes
  checkpoint paths explicitly.

## Forty-image visual review

The deterministic contact sheet at
`artifacts/data_audit/validation_contact_sheet.jpg` was reviewed for the first 40
image records. Boxes generally align with the intended teeth and FDI orientation
appears coherent. The sample exposes meaningful acquisition/appearance variation:
contrast and sharpness shifts, black borders/cropping, side markers, metal
restorations, implants, missing teeth, and overlapping labels in multi-finding
images. These become predefined error-analysis slices; they are not grounds for
silently dropping images.

## License decision

The current Hugging Face card and challenge repository state CC BY-NC-SA 4.0,
while the revised 2025 paper text says CC BY. Until clarified by the dataset owner,
DentXplain applies **CC BY-NC-SA 4.0** to data handling and derived dataset
artifacts. Raw images, annotations, and trained weights will not be redistributed
from this code repository.

## Scientific constraints

- Quadrant-only and quadrant+enumeration records are partially labeled. Missing
  diagnosis labels are unknown, not negative.
- Challenge test labels were historically hidden; current public availability and
  exact ground-truth contents must be verified from the downloaded archives before
  defining a frozen benchmark.
- The public data description alternates between “three institutions with varying
  equipment/protocols” and “one VistaPano S unit under a standardized protocol.”
  Source/institution metadata must be inspected before any domain-shift claim.
- There are no stated patient identifiers in the public schema. A patient-level
  split must not be claimed unless the archive proves otherwise.

## Gate checklist

- [x] Official source, paper, challenge code, and baseline code recorded
- [x] Current archive sizes and local validation archive recorded
- [x] Validation annotation hierarchy confirmed
- [x] Conservative license policy selected
- [x] Validation ZIP integrity and image/annotation pairing confirmed
- [x] At least 40 validation examples visually reviewed
- [ ] Full training archive tree and annotation levels confirmed
- [ ] Duplicate and near-duplicate policy defined
- [ ] Frozen development/test protocol defined without test leakage
- [ ] Disk and GPU budget approved

## Download decision

Do not download the 10.9 GB training archive until validation integrity and visual
audit pass. With approximately 36.7 GB free before extraction, compressed plus
expanded copies require deliberate disk management.

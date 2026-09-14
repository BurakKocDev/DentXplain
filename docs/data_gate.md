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

## Remote training/test archive inspection

The ZIP central directories were read with HTTP byte ranges; the full archives
were not downloaded.

- Training ZIP: 10,927,391,529 compressed bytes, 14,725,611,903 uncompressed
  bytes, 3,603 PNG files and three annotation JSON files.
- Training subsets exactly match the published counts: 693 quadrant images with
  2,772 boxes; 634 quadrant+enumeration images with 18,095 tooth boxes; 705 fully
  annotated images with 3,529 abnormal-tooth boxes; and 1,571 unlabeled images.
- The 705-image fully annotated training JSON has no invalid/orphan/out-of-bounds
  boxes. It includes 2,189 Caries, 604 Impacted, 578 Deep Caries, and 158
  Periapical Lesion annotations. Twenty-seven images have no target annotation.
- Test ZIP: 764,834,414 compressed bytes, 1,028,272,323 uncompressed bytes, 250
  PNG images and 250 per-image LabelMe JSON files.
- The test LabelMe labels use a broader Turkish coded ontology than the four-class
  training COCO schema. The inspected sample includes `çürük`, `küretaj`, `kanal`,
  `çekim`, `gömülü`, `lezyon`, and `kırık`. No unverified collapse of these labels
  into the four benchmark diagnoses is allowed.

## Local training archive and duplicate audit

- `training_data.zip` downloaded at exactly 10,927,391,529 bytes. Its local file
  SHA-256 is `18b2a2dbc5a2b10b0cc6a7677c46a382f4709ab8c9c3bb94f57b74e38e11ffd3`.
- The local central directory matches the remote index: 3,615 entries, 3,603 PNG,
  three JSON, and 14,725,611,903 total uncompressed bytes. The Hugging Face Xet
  object ID is recorded separately and is not treated as the file SHA-256.
- Only the 705-image full-label and 634-image enumeration directories were
  extracted. Both have complete image/annotation pairing and no corrupt or
  dimension-mismatched images.
- The full-label pool has no internal exact duplicates and no exact duplicate in
  the locked 50-image final cohort.
- Source annotations 2335 and 2337 are semantically identical Caries labels for
  `train_377.png`. The conversion keeps the source untouched, records the issue,
  and emits one deterministic YOLO label instead of double-counting it.
- The enumeration pool has nine internal exact-duplicate groups. In addition, 18
  enumeration images are exact copies of locked-final images under different file
  names. These 18 records are excluded from all B1 fitting; internal duplicate
  groups must remain on one side of any B1 split.
- Perceptual hashing is used only to nominate review candidates; it never silently
  merges or removes clinically similar panoramics.

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
- Challenge test labels were historically hidden. They are now present, but use a
  broader raw ontology than the four-class benchmark schema. The test archive is
  exploratory until an owner-supported mapping is documented.
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
- [x] Full training/test archive trees and annotation levels confirmed remotely
- [x] Duplicate and near-duplicate policy defined
- [x] Frozen development/test protocol defined without test leakage
- [x] Disk and GPU budget approved

## Download decision

Validation integrity and visual audit passed. The 10.9 GB training archive was
downloaded and verified. The selected plan keeps the compressed archive
temporarily and extracts only the 705-image full-label directory (~2.69 GB) plus
the 634-image enumeration directory (~2.15 GB), avoiding the full 14.73 GB
expansion. After selective extraction, approximately 19 GiB remained free.

The available NVIDIA GeForce RTX 3050 Ti Laptop GPU has 4 GiB VRAM. B0 starts at
640 px with automatic mixed precision. After the smoke run used less than 0.5 GiB
reported GPU memory, the main run was set to shuffled 960 px square batches of two.
A 1,280 px run is not part of the default plan.

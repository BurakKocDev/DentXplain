from __future__ import annotations

import math
import random
from collections import defaultdict


def stratified_file_split(
    signatures: dict[str, tuple[str, ...]],
    *,
    holdout_fraction: float,
    seed: int,
) -> tuple[list[str], list[str]]:
    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be between zero and one")
    if not signatures:
        raise ValueError("At least one image signature is required")

    by_signature: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    for file_name, signature in signatures.items():
        by_signature[tuple(sorted(signature))].append(file_name)

    target_holdout = round(len(signatures) * holdout_fraction)
    allocations: dict[tuple[str, ...], int] = {}
    fractional: list[tuple[float, tuple[str, ...]]] = []
    for signature, file_names in by_signature.items():
        desired = len(file_names) * holdout_fraction
        allocations[signature] = math.floor(desired)
        fractional.append((desired - math.floor(desired), signature))

    remaining = target_holdout - sum(allocations.values())
    for _, signature in sorted(fractional, key=lambda item: (-item[0], item[1])):
        if remaining == 0:
            break
        allocations[signature] += 1
        remaining -= 1

    generator = random.Random(seed)
    training: list[str] = []
    holdout: list[str] = []
    for signature in sorted(by_signature):
        file_names = sorted(by_signature[signature])
        generator.shuffle(file_names)
        cutoff = allocations[signature]
        holdout.extend(file_names[:cutoff])
        training.extend(file_names[cutoff:])
    return sorted(training), sorted(holdout)

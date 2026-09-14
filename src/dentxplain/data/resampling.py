from __future__ import annotations

from collections.abc import Mapping


def b0_r1_repeat_reason(class_counts: Mapping[str, int]) -> str | None:
    """Return the pre-registered single-repeat reason for a B0 training image."""
    if int(class_counts.get("Periapical Lesion", 0)) > 0:
        return "periapical"
    if int(class_counts.get("Deep Caries", 0)) > int(class_counts.get("Caries", 0)):
        return "deep_caries_dominant"
    return None

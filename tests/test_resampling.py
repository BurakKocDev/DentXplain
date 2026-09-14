from __future__ import annotations

from dentxplain.data import b0_r1_repeat_reason


def test_b0_r1_prioritizes_periapical_images() -> None:
    assert (
        b0_r1_repeat_reason(
            {"Periapical Lesion": 1, "Deep Caries": 3, "Caries": 1}
        )
        == "periapical"
    )


def test_b0_r1_repeats_only_deep_dominant_non_periapical_images() -> None:
    assert b0_r1_repeat_reason({"Deep Caries": 2, "Caries": 1}) == "deep_caries_dominant"
    assert b0_r1_repeat_reason({"Deep Caries": 1, "Caries": 1}) is None
    assert b0_r1_repeat_reason({"Caries": 5}) is None

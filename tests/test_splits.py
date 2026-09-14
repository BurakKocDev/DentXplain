from __future__ import annotations

import pytest

from dentxplain.data import stratified_file_split


def test_stratified_split_is_deterministic_disjoint_and_complete() -> None:
    signatures = {
        **{f"caries_{index}.png": ("Caries",) for index in range(10)},
        **{f"impacted_{index}.png": ("Impacted",) for index in range(5)},
        **{f"empty_{index}.png": ("NO_TARGET_ANNOTATION",) for index in range(5)},
    }

    first = stratified_file_split(signatures, holdout_fraction=0.2, seed=7)
    second = stratified_file_split(signatures, holdout_fraction=0.2, seed=7)

    assert first == second
    training, holdout = first
    assert len(training) == 16
    assert len(holdout) == 4
    assert set(training).isdisjoint(holdout)
    assert set(training) | set(holdout) == set(signatures)
    assert sum(name.startswith("caries_") for name in holdout) == 2


def test_stratified_split_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        stratified_file_split({"a.png": ("A",)}, holdout_fraction=1.0, seed=1)
    with pytest.raises(ValueError, match="At least one"):
        stratified_file_split({}, holdout_fraction=0.2, seed=1)

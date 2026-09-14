from __future__ import annotations

from pathlib import Path

import pytest

from dentxplain.evaluation import summarize_results

HEADER = (
    "epoch,time,train/box_loss,train/cls_loss,train/dfl_loss,"
    "metrics/precision(B),metrics/recall(B),metrics/mAP50(B),metrics/mAP50-95(B),"
    "val/box_loss,val/cls_loss,val/dfl_loss,lr/pg0,lr/pg1,lr/pg2\n"
)


def test_summary_selects_best_development_epoch(tmp_path: Path) -> None:
    results = tmp_path / "results.csv"
    results.write_text(
        HEADER
        + "1,1,1,2,3,.1,.2,.3,.15,4,5,6,0,0,0\n"
        + "2,2,.9,1.9,2.9,.4,.5,.6,.35,3.9,4.9,5.9,0,0,0\n"
        + "3,3,.8,1.8,2.8,.3,.4,.5,.25,3.8,4.8,5.8,0,0,0\n",
        encoding="utf-8",
    )

    summary = summarize_results(results)

    assert summary["completed_epochs"] == 3
    assert summary["best"]["epoch"] == 2
    assert summary["best"]["metrics/mAP50-95(B)"] == pytest.approx(0.35)
    assert summary["last"]["epoch"] == 3


def test_summary_rejects_empty_results(tmp_path: Path) -> None:
    results = tmp_path / "results.csv"
    results.write_text(HEADER, encoding="utf-8")

    with pytest.raises(ValueError, match="No completed epochs"):
        summarize_results(results)

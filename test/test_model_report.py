"""Ensure the saved evaluation describes the actual inference artifacts."""
import csv
import hashlib
import json
from pathlib import Path
from sklearn.metrics import f1_score
from ai.inference import EnsemblePredictor
from scripts.train_evaluate import group_key

ROOT = Path(__file__).resolve().parents[1]


def test_holdout_report_matches_current_inference_and_artifact_hashes():
    directory = ROOT / "ai/artifacts/prototype"
    report = json.loads((directory / "evaluation.json").read_text(encoding="utf-8"))
    for artifact in report["artifact_files"].values():
        assert hashlib.sha256((directory / artifact["file"]).read_bytes()).hexdigest() == artifact["sha256"]
    with (ROOT / "crawl/data_clean.csv").open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    test_groups = set(report["split"]["test_group_hashes"])
    heldout = [row for row in rows if group_key(row["content"]) in test_groups]
    assert len(heldout) == report["split"]["test"] == 97
    predictions = EnsemblePredictor(model_dir=directory).predict(heldout)
    for target, label in (("urgency", "label"), ("reliability", "confident")):
        actual = [row[label].strip().upper() for row in heldout]
        predicted = [row[target + "_label"] for row in predictions]
        assert abs(f1_score(actual, predicted, average="macro") - report["targets"][target]["ensemble"]["macro_f1"]) < 1e-12
    assert all(item["model_version"] == report["model_version"] for item in predictions)

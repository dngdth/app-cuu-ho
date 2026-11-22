"""Reproducible grouped holdout + training-only tuning/calibration; no source mutation."""
import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import classification_report, confusion_matrix, f1_score, log_loss
from sklearn.model_selection import GridSearchCV, GroupShuffleSplit, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from lightgbm import LGBMClassifier
from ai.features import normalize_record, prepare_features
from ai.inference import MODEL_FILES
from ai.src.props import ALLOWED_NEEDS
from app.services.address_utils import PROVINCE_NAMES

CATEGORICAL = ["tinh_tp", "disaster_type", "is_isolated", "deathly", "infrastructure_damage",
               "has_emergency_terms", "has_emotional_terms", "has_emphasis", "contact", "location"]
NUMERIC = ["affected_people_log", "reactions", "replies", "humanitarian_need_score", "rescue_need_score", *ALLOWED_NEEDS]


def group_key(text):
    return hashlib.sha256(re.sub(r"\W+", " ", text.casefold()).strip().encode()).hexdigest()


def split_groups(rows, groups, targets):
    for seed in range(42, 100):
        fitcal, test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed).split(rows, groups=groups))
        fit_rel, cal_rel = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed + 1).split(fitcal, groups=groups[fitcal]))
        fit, cal = fitcal[fit_rel], fitcal[cal_rel]
        if all(set(y[fit]) == set(y[cal]) == set(y[test]) == set(y) for y in targets.values()):
            return fit, cal, test, seed
    raise ValueError("Không đủ lớp trong các nhóm để chia train/calibration/test độc lập")


def preprocessor():
    return ColumnTransformer([
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CATEGORICAL),
        ("num", Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value=0))]), NUMERIC),
    ], remainder="drop")


def metrics(y, probability, encoder):
    pred = probability.argmax(axis=1)
    return {"macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
            "log_loss": float(log_loss(y, probability, labels=np.arange(len(encoder.classes_)))),
            "classes": encoder.classes_.tolist(),
            "classification_report": classification_report(y, pred, target_names=encoder.classes_, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(y, pred, labels=np.arange(len(encoder.classes_))).tolist()}


def train(source, output):
    output.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8-sig") as stream:
        raw = list(csv.DictReader(stream))
    rows = [normalize_record(row) for row in raw]
    groups = np.array([group_key(row["content"]) for row in rows])
    targets = {"urgency": np.array([row["label"].strip().upper() for row in raw]),
               "reliability": np.array([row["confident"].strip().upper() for row in raw])}
    fit, cal, test, seed = split_groups(rows, groups, targets)
    frame = prepare_features(rows, PROVINCE_NAMES)
    for column in CATEGORICAL:
        frame[column] = frame[column].astype(str)
    frame = frame[CATEGORICAL + NUMERIC]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(),
        "data_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "rows": len(rows),
        "split": {"train": len(fit), "calibration": len(cal), "test": len(test), "seed": seed,
            "group_intersection": len(set(groups[fit]) & set(groups[test]) | set(groups[cal]) & set(groups[test])),
            "test_group_hashes": sorted(set(groups[test]))},
        "limitations": ["Nhãn trong data_clean.csv chưa được kiểm toán bằng chuyên gia hoặc nguồn xác minh độc lập.",
            "Đây là kiểm tra holdout nội bộ từ dữ liệu crawl hiện có; chưa phải đánh giá ngoài thực địa.",
            "Không dùng tập test để chọn tham số. Calibration dùng nhóm riêng bên trong tập phát triển.",
            "Độ tin cậy mô hình không xác thực tính đúng/sai của bài đăng."], "targets": {}}
    report["code_sha256"] = hashlib.sha256(Path(__file__).read_bytes() + (Path(__file__).resolve().parents[1] / "ai/features.py").read_bytes()).hexdigest()
    report["model_version"] = hashlib.sha256((report["data_sha256"] + report["code_sha256"]).encode()).hexdigest()[:12]
    artifacts = {name: {"format_version": 2, "categorical_columns": CATEGORICAL, "province_vocabulary": list(PROVINCE_NAMES)} for name in MODEL_FILES}
    for target, labels in targets.items():
        encoder = LabelEncoder().fit(labels[fit])
        y = encoder.transform(labels)
        model_key, encoder_key = ("model_label", "le_label") if target == "urgency" else ("model_conf", "le_conf")
        results, probabilities = {}, []
        baseline = DummyClassifier(strategy="prior").fit(frame.iloc[fit], y[fit])
        results["baseline"] = metrics(y[test], baseline.predict_proba(frame.iloc[test]), encoder)
        options = {
            "gradient_boosting": (GradientBoostingClassifier(random_state=seed, n_estimators=60), {"classifier__max_depth": [2, 3]}),
            "random_forest": (RandomForestClassifier(random_state=seed, n_estimators=100, n_jobs=1, class_weight="balanced"), {"classifier__min_samples_leaf": [2, 4]}),
            "lightgbm": (LGBMClassifier(random_state=seed, n_estimators=70, verbosity=-1, n_jobs=1, class_weight="balanced"), {"classifier__num_leaves": [7, 15]}),
        }
        for name, (classifier, params) in options.items():
            pipeline = Pipeline([("preprocessor", preprocessor()), ("classifier", classifier)])
            search = GridSearchCV(pipeline, params, cv=StratifiedGroupKFold(3, shuffle=True, random_state=seed),
                                  scoring="f1_macro", n_jobs=1, refit=True, error_score="raise")
            search.fit(frame.iloc[fit], y[fit], groups=groups[fit])
            selected = search.best_estimator_
            uncalibrated = metrics(y[test], selected.predict_proba(frame.iloc[test]), encoder)
            prep = selected.named_steps["preprocessor"]
            calibrated = CalibratedClassifierCV(FrozenEstimator(selected.named_steps["classifier"]), method="sigmoid")
            calibrated.fit(prep.transform(frame.iloc[cal]), y[cal])
            calibrated_model = Pipeline([("preprocessor", prep), ("classifier", calibrated)])
            probability = calibrated_model.predict_proba(frame.iloc[test])
            probabilities.append(probability)
            results[name] = metrics(y[test], probability, encoder)
            results[name].update(best_parameters=search.best_params_, inner_cv_macro_f1=float(search.best_score_),
                                 before_calibration=uncalibrated)
            artifacts[name][model_key] = calibrated_model
            artifacts[name][encoder_key] = encoder
            print(f"{target} {name}: F1={results[name]['macro_f1']:.3f}", flush=True)
        averaged = np.mean(probabilities, axis=0)
        results["ensemble"] = metrics(y[test], averaged, encoder)
        # Post-hoc explanation only. This does not feed model/parameter selection.
        important = permutation_importance(artifacts["gradient_boosting"][model_key], frame.iloc[test], y[test],
            scoring="f1_macro", n_repeats=2, random_state=seed, n_jobs=1)
        ranking = sorted(zip(frame.columns, important.importances_mean), key=lambda pair: pair[1], reverse=True)
        results["global_explanation"] = [{"feature": column, "macro_f1_decrease": float(value)} for column, value in ranking[:12]]
        report["targets"][target] = results
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        matrix = np.array(results["ensemble"]["confusion_matrix"])
        axes[0].imshow(matrix, cmap="Blues")
        axes[0].set(title=f"{target}: grouped holdout", xlabel="Predicted", ylabel="Actual",
                    xticks=range(len(encoder.classes_)), yticks=range(len(encoder.classes_)),
                    xticklabels=encoder.classes_, yticklabels=encoder.classes_)
        for (i, j), value in np.ndenumerate(matrix):
            axes[0].text(j, i, str(value), ha="center", va="center")
        axes[1].barh([r[0] for r in ranking[:8]][::-1], [r[1] for r in ranking[:8]][::-1])
        axes[1].set(title="Permutation importance (Gradient Boosting)", xlabel="Decrease in macro F1")
        fig.tight_layout()
        fig.savefig(output / f"{target}_evaluation.png", dpi=160)
        plt.close(fig)
    for name, artifact in artifacts.items():
        joblib.dump(artifact, output / MODEL_FILES[name])
    report["method"] = "calibrated_average"
    report["artifact_files"] = {name: {"file": filename, "sha256": hashlib.sha256((output / filename).read_bytes()).hexdigest()}
                                for name, filename in MODEL_FILES.items()}
    (output / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps({"format_version": 2, "method": "calibrated_average",
        "version": report["model_version"], "evaluation": "evaluation.json", "trained_at": report["generated_at"]}, indent=2), encoding="utf-8")
    print(json.dumps({"split": {k: v for k, v in report["split"].items() if k != "test_group_hashes"}, "report": str(output / "evaluation.json")}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("crawl/data_clean.csv"))
    parser.add_argument("--output", type=Path, default=Path("ai/artifacts/prototype"))
    args = parser.parse_args()
    train(args.source, args.output)

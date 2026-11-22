"""Load existing artifacts once and predict every input row independently."""
import os
import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from ai.features import normalize_record, prepare_features

MODEL_FILES = {
    "gradient_boosting": "rescue_model.pkl",
    "random_forest": "rescue_model_rf.pkl",
    "lightgbm": "rescue_model_lightGBM.pkl",
}
SCORES = {"THẤP": 1.0, "TRUNG BÌNH": 2.0, "CAO": 3.0}


@lru_cache(maxsize=8)
def load_model(path):
    brain = joblib.load(path)
    # API requests already run in worker threads. Avoid spawning a CPU-wide pool
    # for each small prediction batch (and sharing nested sklearn thread state).
    for name in ("model_label", "model_conf"):
        classifier = brain[name].named_steps["classifier"]
        if "n_jobs" in classifier.get_params():
            classifier.set_params(n_jobs=1)
    return brain


def predict_artifact(frame, path):
    brain = load_model(str(Path(path).resolve()))
    data = frame.copy()
    if brain.get("format_version") == 2:
        for key in brain["categorical_columns"]:
            data[key] = data[key].astype(str)
    # The saved LightGBM one-hot encoder expects these exact strings.
    elif "has_emotional_terms" in brain["model_label"].feature_names_in_:
        for key in ("has_emotional_terms", "has_emphasis"):
            data[key] = data[key].map(lambda value: str(bool(value)))
        for key in ("contact", "location"):
            data[key] = data[key].astype(int).astype(str)
    results = {}
    for target, model_key, encoder_key in (
        ("urgency", "model_label", "le_label"),
        ("reliability", "model_conf", "le_conf"),
    ):
        model = brain[model_key]
        probabilities = model.predict_proba(data)
        predicted = model.classes_[probabilities.argmax(axis=1)]
        results[target] = brain[encoder_key].inverse_transform(predicted.astype(int))
        results[target + "_probability"] = np.max(probabilities, axis=1)
        classes = brain[encoder_key].inverse_transform(model.classes_.astype(int))
        results[target + "_distribution"] = [{str(label).strip().upper(): float(value) for label, value in zip(classes, row, strict=True)} for row in probabilities]
    return results


class EnsemblePredictor:
    def __init__(self, model_dir=None):
        self.model_dir = Path(model_dir or os.getenv("RESCUE_MODEL_DIR") or Path(__file__).parent)

    def predict(self, records):
        rows = [normalize_record(record) for record in records]
        if not rows:
            return []
        first = load_model(str((self.model_dir / MODEL_FILES["gradient_boosting"]).resolve()))
        calibrated = first.get("format_version") == 2
        manifest_path = self.model_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
        provinces = first.get("province_vocabulary") or first["model_label"][0].named_transformers_["cat"]["onehot"].categories_[0]
        frame = prepare_features(rows, provinces)
        predictions = {name: predict_artifact(frame, self.model_dir / filename)
                       for name, filename in MODEL_FILES.items()}
        output = []
        for index, row in enumerate(rows):
            details = {name: {
                "urgency_label": str(result["urgency"][index]).strip().upper(),
                "urgency_probability": float(result["urgency_probability"][index]),
                "reliability_label": str(result["reliability"][index]).strip().upper(),
                "reliability_probability": float(result["reliability_probability"][index]),
                "urgency_distribution": result["urgency_distribution"][index],
                "reliability_distribution": result["reliability_distribution"][index],
            } for name, result in predictions.items()}
            urgency_model = max(details, key=lambda name: details[name]["urgency_probability"])
            reliability_model = max(details, key=lambda name: details[name]["reliability_probability"])
            urgency = details[urgency_model]["urgency_label"]
            reliability = details[reliability_model]["reliability_label"]
            urgency_probability = details[urgency_model]["urgency_probability"]
            reliability_probability = details[reliability_model]["reliability_probability"]
            if calibrated:
                averages = {}
                for target in ("urgency", "reliability"):
                    labels = {label for model in details.values() for label in model[target + "_distribution"]}
                    averages[target] = {label: float(np.mean([model[target + "_distribution"].get(label, 0) for model in details.values()])) for label in labels}
                urgency = max(averages["urgency"], key=averages["urgency"].get)
                reliability = max(averages["reliability"], key=averages["reliability"].get)
                urgency_probability, reliability_probability = averages["urgency"][urgency], averages["reliability"][reliability]
                urgency_model = reliability_model = "calibrated_ensemble"
            output.append({
                "record": row,
                "urgency_label": urgency, "urgency_score": SCORES[urgency],
                "reliability_label": reliability, "reliability_score": SCORES[reliability],
                "urgency_probability": urgency_probability,
                "reliability_probability": reliability_probability,
                "urgency_model": urgency_model, "reliability_model": reliability_model,
                "models": details,
                "method": "calibrated_average" if calibrated else "highest_probability",
                "model_version": manifest.get("version", "legacy"),
            })
        return output

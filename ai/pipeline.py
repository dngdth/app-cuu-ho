"""Public entry point for structured records from a bot, CSV, or Python client."""
import pandas as pd

from ai.inference import EnsemblePredictor


def run_processing_data(raw_data, client=None):
    if isinstance(raw_data, pd.DataFrame):
        records = raw_data.to_dict(orient="records")
    else:
        records = raw_data if isinstance(raw_data, list) else [raw_data]
        records = [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in records]
    if client is not None:
        return client.process_data(records)
    return EnsemblePredictor().predict(records)

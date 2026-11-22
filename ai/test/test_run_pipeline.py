"""The old import remains usable without a globally configured bot or HTTP client."""
from ai.pipeline import run_processing_data
from ai.test.pipeline import run_processing_data as legacy_pipeline


def test_legacy_pipeline_uses_production_entry_point():
    assert legacy_pipeline is run_processing_data


def test_pipeline_can_send_structured_data_to_api():
    captured = []

    class Client:
        def process_data(self, records):
            captured.extend(records)
            return {"created": len(records)}

    result = run_processing_data([{"content": "Cần cứu hộ", "location": "Huế"}], client=Client())
    assert result == {"created": 1}
    assert captured[0]["location"] == "Huế"

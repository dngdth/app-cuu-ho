"""Compatibility entry point; the application pipeline now lives outside test/."""
from ai.pipeline import run_processing_data

__all__ = ["run_processing_data"]

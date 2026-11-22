import pandas as pd
import re
from pydantic import BaseModel
from module.agent import Agent
from dataclasses import asdict, is_dataclass


def raw_to_dataframe(raw_data_from_bot) -> pd.DataFrame:
    """
    raw_data_from_bot là Pydantic BaseModel (hoặc list BaseModel).
    Trả về pandas DataFrame.
    Hỗ trợ cả Pydantic v1 (.dict) và v2 (.model_dump).
    """

    def dump_pydantic(obj):
        # Pydantic v2
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # Pydantic v1
        if hasattr(obj, "dict"):
            return obj.dict()
        raise TypeError("Đầu vào không phải Pydantic BaseModel")

    # Case 1: list BaseModel
    if isinstance(raw_data_from_bot, list):
        return pd.DataFrame([dump_pydantic(x) for x in raw_data_from_bot])

    # Case 2: single BaseModel
    return pd.DataFrame([dump_pydantic(raw_data_from_bot)])
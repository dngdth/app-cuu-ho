"""Normalize source records without destroying addresses or contacts."""
import ast
import json
import math
import re

import numpy as np
import pandas as pd

from ai.src.props import ALLOWED_NEEDS
from ai.src.prompts_utils import extract_string_features
from ai.address_extraction import extract_address, missing_address


def nullable(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, str) and value.strip().lower() in ("", "null", "none", "nan"):
        return None
    return value.strip() if isinstance(value, str) else value


def boolean(value):
    value = nullable(value)
    if value is None:
        return False
    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes", "có", "x"):
            return True
        if value.lower() in ("false", "0", "no", "không"):
            return False
        raise ValueError(f"Invalid boolean: {value}")
    if value in (True, False, 0, 1):
        return bool(value)
    raise ValueError("Boolean must be true/false or 1/0")


def list_values(value):
    value = nullable(value)
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if nullable(v) is not None]
    text = str(value).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = ast.literal_eval(text)
        if not isinstance(parsed, list):
            raise ValueError("Expected a list")
        return list_values(parsed)
    return [v.strip() for v in text.split(",") if v.strip()]


def normalize_record(record):
    row = {key: nullable(value) for key, value in dict(record).items()}
    row["content"] = str(row.get("content") or "").strip()
    if not row["content"]:
        raise ValueError("content is required")
    string_features = extract_string_features(row["content"])
    for canonical, alias in (("has_emergency_terms", "has_emergency"),
                             ("has_emotional_terms", "has_emotion")):
        value = row.get(canonical) if row.get(canonical) is not None else row.get(alias)
        row[canonical] = boolean(value) if value is not None else string_features[canonical]
    for key in ("is_isolated", "deathly", "infrastructure_damage", "has_emphasis"):
        value = row.get(key)
        row[key] = boolean(value) if value is not None else string_features.get(key, False)
    for key in ("affected_people", "reactions", "replies"):
        value = row.get(key)
        if value is None:
            row[key] = None if key == "affected_people" else 0
        else:
            number = float(value)
            if not math.isfinite(number) or number < 0 or not number.is_integer():
                raise ValueError(f"{key} must be a non-negative integer")
            row[key] = int(number)
    raw_contact = row.get("contact")
    binary_contact = raw_contact is not None and str(raw_contact) in ("0", "1")
    row["contact_present"] = bool(int(raw_contact)) if binary_contact else bool(row.get("contact_present"))
    if binary_contact or not raw_contact:
        phones = re.findall(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9,10}(?!\d)", row["content"])
        row["contact"] = ", ".join(dict.fromkeys(phones)) or None
    elif isinstance(raw_contact, list) or str(raw_contact).startswith("["):
        row["contact"] = ", ".join(list_values(raw_contact)) or None
    else:
        row["contact"] = str(raw_contact)
    row["contact_present"] = row["contact_present"] or bool(row["contact"])
    row["needs"] = list_values(row.get("needs", row.get("needs_text")))
    raw_disaster = row.get("disaster_type", row.get("disaster_type_text"))
    if raw_disaster is not None and str(raw_disaster).isdigit():
        row["disaster_code"] = int(raw_disaster)
        row["disaster_type"] = []
    else:
        row["disaster_type"] = list_values(raw_disaster)
    row["location"] = str(row["location"]) if row.get("location") else None
    if missing_address(row["location"]):
        extracted = extract_address(row["content"])
        if extracted:
            row["location"], row["location_extracted"] = extracted, True
    return row


def disaster_code(types):
    # data_v5.csv: unknown=0, single=1, combined=2, landslide combinations=3.
    known = {v.lower() for v in types} - {"không xác định", "không rõ"}
    if not known:
        return 0
    if len(known) > 1 and "sạt lở" in known:
        return 3
    return min(len(known), 2)


def prepare_features(records, provinces=()):
    feature_rows = []
    for row in records:
        feature = dict(row)
        address = (row.get("location") or "").casefold()
        feature["tinh_tp"] = row.get("tinh_tp") or next(
            (p for p in sorted(provinces, key=len, reverse=True)
             if p.casefold() in address and p not in ("Tỉnh", "Unknown", "TN", "cậy")), "Unknown")
        feature["disaster_type"] = row.get("disaster_code", disaster_code(row["disaster_type"]))
        for need in ALLOWED_NEEDS:
            feature[need] = int(need in row["needs"] or boolean(row.get(need)))
        feature["humanitarian_need_score"] = sum(feature[n] for n in ALLOWED_NEEDS[:3])
        feature["rescue_need_score"] = feature[ALLOWED_NEEDS[3]] + feature[ALLOWED_NEEDS[5]]
        feature["affected_people"] = row["affected_people"] or 0
        feature["affected_people_log"] = np.log1p(feature["affected_people"])
        feature["contact"] = int(row["contact_present"])
        feature["location"] = int(bool(row.get("location")))
        feature_rows.append(feature)
    return pd.DataFrame(feature_rows)

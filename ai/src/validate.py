from .props import ALLOWED_NEEDS, ALLOWED_DISASTER_TYPES
import json


def validate_keys(data: dict, required_keys: list) -> bool:
    """Check tất cả key bắt buộc có trong data"""
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        print(f"[WARN] Thiếu key: {missing_keys}")
        return False
    return True


def validate_types(data: dict, expected_types: dict) -> bool:
    """Check kiểu dữ liệu của các key"""
    valid = True
    for key, t in expected_types.items():
        if key not in data:
            continue
        if not isinstance(data[key], t):
            print(
                f"[WARN] Key '{key}' kiểu dữ liệu sai: {type(data[key])}, expected {t}"
            )
            valid = False
    return valid


def validate_needs(data: dict, allowed_needs: list) -> bool:
    """Check tất cả phần tử trong needs hợp lệ"""
    if "needs" not in data or not isinstance(data["needs"], list):
        return False
    invalid = [n for n in data["needs"] if n not in allowed_needs]
    if invalid:
        print(f"[WARN] Needs có giá trị không hợp lệ: {invalid}")
        return False
    return True


def validate_disaster_type(data: dict, allowed_types: list) -> bool:
    """Check tất cả phần tử trong disaster_type hợp lệ"""
    if "disaster_type" not in data or not isinstance(data["disaster_type"], list):
        return False
    invalid = [t for t in data["disaster_type"] if t not in allowed_types]
    if invalid:
        print(f"[WARN] Disaster type có giá trị không hợp lệ: {invalid}")
        return False
    return True


def clean_data(data: dict) -> dict:
    """Chuẩn hóa JSON: null -> None, contact string -> list, lọc needs và disaster_type"""
    cleaned = {}
    for k, v in data.items():
        if v == "null" or v is None:
            cleaned[k] = [] if k in ["needs", "disaster_type"] else None
        elif k == "needs":
            cleaned[k] = [x for x in v if x in ALLOWED_NEEDS]
        elif k == "disaster_type":
            # Nếu là list, lọc các giá trị hợp lệ
            if isinstance(v, list):
                cleaned[k] = [x for x in v if x in ALLOWED_DISASTER_TYPES]
            else:
                cleaned[k] = []
        elif k == "contact" and isinstance(v, str):
            cleaned[k] = [v]
        else:
            cleaned[k] = v
    return cleaned

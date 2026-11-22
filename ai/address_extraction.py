"""Explicit source-address markers only; no guessed household locations."""
import re


def missing_address(value):
    return str(value or "").strip().casefold() in ("", "không rõ", "không xác định", "unknown", "0", "1")


def extract_address(content):
    match = re.search(r"(?:địa\s*chỉ|đ/c|đc)\s*[:：]\s*([^\n]+)", str(content or ""), re.I)
    if not match:
        return None
    address = re.split(r"(?:\s+(?:sđt|sdt|điện thoại|liên hệ)\s*[:：]?)|(?:[.!?](?:\s|$))", match[1], maxsplit=1, flags=re.I)[0].strip(" ,;-")[:2000]
    return address or None

"""Conservative local extraction. Missing facts stay missing for human review."""
import re
from ai.features import normalize_record
from app.services.google_maps_service import map_links
from ai.address_extraction import extract_address

DISASTERS = {"lũ lụt": ("ngập", "lụt", "nước dâng"), "sạt lở": ("sạt lở", "lở đất"), "bão": ("bão",)}
NEEDS = {"lương thực & nước uống": ("lương thực", "đồ ăn", "thức ăn", "nước uống", "mì gói"),
         "y tế": ("thuốc", "cấp cứu", "y tế"), "phương tiện & cứu hộ": ("cứu hộ", "cứu giúp", "thuyền", "xuồng"),
         "nhu yếu phẩm": ("chăn", "quần áo", "nhu yếu phẩm")}


def extract_post(content, source_url=None):
    text = str(content or "").strip()
    if not text or len(text) > 20000:
        raise ValueError("Nội dung cần có từ 1 đến 20.000 ký tự")
    lower = text.lower()
    location = extract_address(text)
    people = re.search(r"(?<!\d)(\d{1,5})\s*(?:người|thành viên)(?!\w)", lower)
    row = {"content": text, "location": location, "source_url": source_url,
           "map_link": next(iter(map_links(text)), None),
           "affected_people": int(people[1]) if people else None,
           "needs": [name for name, terms in NEEDS.items() if any(term in lower for term in terms)],
           "disaster_type": [name for name, terms in DISASTERS.items() if any(term in lower for term in terms)],
           "extraction_source": "local_rules", "extraction_review_required": True,
           "status": "unverified"}
    return normalize_record(row)

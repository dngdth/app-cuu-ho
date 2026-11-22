"""Provider-neutral, conservative matching of a stated Vietnamese address."""
import re
from app.services.address_utils import PROVINCE_NAMES, expected_provinces, folded

ADDRESS_TYPES = {"street_address", "premise", "subpremise", "establishment", "point_of_interest"}
STOP_WORDS = {"nha", "so", "duong", "hem", "kiet", "ngo", "dia", "chi", "thon", "xom"}


def address_variants(address):
    address = re.sub(r"\s+", " ", str(address or "")).strip()
    address = re.sub(r"^địa chỉ\s*:\s*", "", address, flags=re.IGNORECASE)
    variants = [address] if address else []
    match = re.match(r"^(\d+[A-Za-z]?)\s*/\s*(\d+[A-Za-z]?)\s+([^/].*)$", address)
    if match:
        alley = "kiệt" if "hue" in folded(address) else "hẻm"
        variants.append(f"{match[1]} {alley} {match[2]} {match[3]}")
    return list(dict.fromkeys(variants))


def structured_address(address):
    """Separate explicit house/alley, street and province; never invent a city."""
    parts = [part.strip() for part in str(address or "").split(",")]
    first = re.sub(r"^(?:nhà\s+số|số|nhà)\s+", "", parts[0], flags=re.IGNORECASE)
    match = re.fullmatch(r"(\d+[A-Za-z]?(?:\s*/\s*\d+[A-Za-z]?)*)\s+(.+)", first)
    if not match:
        return None
    house, street = re.sub(r"\s+", "", match[1]), match[2]
    alley = re.fullmatch(r"(?:kiệt|hẻm|ngõ)\s+(\d+[A-Za-z]?)\s+(.+)", street, flags=re.IGNORECASE)
    if alley:
        house, street = f"{house}/{alley[1]}", alley[2]
    provinces = {folded(name) for name in PROVINCE_NAMES}
    for part in reversed(parts[1:]):
        region = re.sub(r"^(?:thành phố|tỉnh|tp\.?)\s+", "", part, flags=re.IGNORECASE)
        name = folded(region)
        if name not in provinces:
            continue
        field = "city" if name in {"hue", "thua thien hue", "ha noi", "ho chi minh", "da nang", "hai phong"} else "state"
        if name == "thua thien hue":
            region = "Huế"
        return {"housenumber": house, "street": street, field: region}
    return None


def street_key(street):
    return re.sub(r"^(?:duong|pho)\s+", "", folded(str(street or ""))).strip()


def matching_candidate(original, candidate):
    formatted = candidate.get("formatted_address") or candidate.get("formattedAddress") or ""
    components = candidate.get("address_components", candidate.get("addressComponents", []))
    countries = [item.get("short_name", item.get("shortText", "")).upper() for item in components if "country" in item.get("types", [])]
    if countries != ["VN"]:
        return "wrong_country"
    expected, actual = expected_provinces(original), folded(formatted)
    if expected and not any(re.search(r"\b" + re.escape(name) + r"\b", actual) for name in expected):
        return "wrong_region"
    tokens = set(re.findall(r"[a-z]+|\d+[a-z]?", folded(original.split(",")[0]))) - STOP_WORDS
    actual_tokens = set(re.findall(r"[a-z]+|\d+[a-z]?", actual))
    if not tokens or not tokens.issubset(actual_tokens):
        return "address_mismatch"
    if candidate.get("partial_match"):
        return "partial_match"
    if not ADDRESS_TYPES.intersection(candidate.get("types", [])):
        return "area_or_street_center"
    return None

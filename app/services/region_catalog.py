"""Match explicit province names; never infer a household position from a province."""
import re
from app.models.region_model import Region
from app.services.address_utils import folded, PROVINCE_NAMES


def region_key(name):
    value = folded(name).strip()
    value = re.sub(r"^(thanh pho|tinh|tp\.?)[ .]*", "", value)
    return {"hcm": "ho chi minh", "hue": "hue", "thua thien hue": "hue"}.get(value, value)


def ensure_catalog(db):
    # Include historic names too: old source addresses must stay searchable.
    existing = {region_key(row.name) for row in db.query(Region).filter(Region.parent_id.is_(None))}
    for name in PROVINCE_NAMES:
        key = region_key(name)
        if key not in existing:
            db.add(Region(name=name))
            existing.add(key)
    db.flush()


def find_region(db, address):
    if not address or str(address).strip().startswith(("http://", "https://")):
        return None
    regions = list(db.query(Region).filter(Region.parent_id.is_(None)))
    by_key = {region_key(row.name): row.id for row in regions}
    # A comma-separated administrative suffix is stronger than arbitrary text.
    for part in reversed(str(address).split(",")):
        key = region_key(part)
        if key in by_key:
            return by_key[key]
    text = " " + folded(address) + " "
    matches = {row.id for row in regions if re.search(r"(?<!\w)" + re.escape(region_key(row.name)) + r"(?!\w)", text)}
    return next(iter(matches)) if len(matches) == 1 else None

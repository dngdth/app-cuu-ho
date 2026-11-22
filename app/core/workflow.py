"""Human review lifecycle, independent of AI scores."""
TRANSITIONS = {
    "unverified": ("pending", "rejected"),
    "pending": ("in_progress", "rejected"),
    "in_progress": ("resolved", "pending"),
    "resolved": ("pending",),
    "rejected": ("unverified",),
}


def canonical_status(value):
    return value if value in TRANSITIONS else "unverified"


def next_statuses(value):
    return list(TRANSITIONS[canonical_status(value)])

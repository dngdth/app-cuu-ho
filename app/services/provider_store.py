"""Shared, durable API limits. Reservations survive failures and worker restarts."""
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from app.db.database import SessionLocal
from app.models.operations_model import ApiCounter, ProviderCache
from app.core import config


class ProviderLimit(Exception):
    pass


def limits(service):
    if service == "geocoding":
        return config.GEOCODING_DAILY_LIMIT, config.GEOCODING_MONTHLY_LIMIT
    if service == "routing":
        return config.ROUTING_DAILY_LIMIT, config.ROUTING_MONTHLY_LIMIT
    raise ValueError("Unknown provider service")


def cache_key(service, params):
    return hashlib.sha256(json.dumps([service, params], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ProviderStore:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def cached(self, key):
        with self.session_factory() as db:
            row = db.get(ProviderCache, key)
            if row and row.expires_at > datetime.now(timezone.utc):
                return row.payload
        return None

    def remember(self, key, payload, seconds=86400):
        with self.session_factory() as db:
            statement = insert(ProviderCache).values(key=key, payload=payload,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=seconds))
            db.execute(statement.on_conflict_do_update(index_elements=[ProviderCache.key],
                set_={"payload": statement.excluded.payload, "expires_at": statement.excluded.expires_at}))
            db.commit()

    def reserve(self, service):
        daily, monthly = limits(service)
        now = datetime.now(timezone.utc)
        periods = [("day", now.strftime("%Y-%m-%d"), daily), ("month", now.strftime("%Y-%m"), monthly)]
        with self.session_factory() as db:
            # One stable lock order across threads and processes. Do not reset on key rotation.
            db.execute(select(func.pg_advisory_xact_lock(1415, 0)))
            second = str(int(time.time()))
            db.execute(insert(ApiCounter).values(service="all", period="second", period_key=second, count=0).on_conflict_do_nothing())
            rate = db.get(ApiCounter, ("all", "second", second))
            if rate.count >= 2:
                raise ProviderLimit("local_rate_limit")
            rows = []
            for period, key, limit in periods:
                db.execute(insert(ApiCounter).values(service=service, period=period, period_key=key, count=0)
                           .on_conflict_do_nothing())
                row = db.get(ApiCounter, (service, period, key))
                if limit <= 0 or row.count >= limit:
                    raise ProviderLimit("local_quota_exceeded")
                rows.append(row)
            for row in rows:
                row.count += 1
            rate.count += 1
            db.commit()


def usage_summary(db):
    now = datetime.now(timezone.utc)
    result = {}
    for service in ("geocoding", "routing"):
        daily, monthly = limits(service)
        day = db.get(ApiCounter, (service, "day", now.strftime("%Y-%m-%d")))
        month = db.get(ApiCounter, (service, "month", now.strftime("%Y-%m")))
        result[service] = {"day_used": day.count if day else 0, "day_limit": daily,
                           "month_used": month.count if month else 0, "month_limit": monthly}
    return {"provider": "geoapify", "timezone": "UTC", "services": result}

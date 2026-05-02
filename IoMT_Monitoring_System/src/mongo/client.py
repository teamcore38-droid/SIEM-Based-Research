from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient

from src.common.settings import get_settings


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured")
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)


def get_database():
    settings = get_settings()
    return get_client()[settings.mongodb_db]


def ping_database() -> bool:
    client = get_client()
    client.admin.command("ping")
    return True


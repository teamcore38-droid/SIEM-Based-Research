from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from src.common.models import utc_now_iso
from src.common.settings import get_settings
from src.mongo.client import get_database


class SensorLogRepository:
    def __init__(self):
        settings = get_settings()
        db = get_database()
        self.collection = db[settings.sensor_collection]

    def insert_one(self, document: Dict[str, Any]):
        return self.collection.insert_one(document)

    def insert_many(self, documents: Iterable[Dict[str, Any]]):
        docs = list(documents)
        if not docs:
            return None
        return self.collection.insert_many(docs)

    def latest(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self.collection.find().sort("_id", -1).limit(limit))

    def recent_for_device(self, device_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        return list(self.collection.find({"device_id": device_id}).sort("_id", -1).limit(limit))

    def count(self) -> int:
        return self.collection.count_documents({})

    def attack_count(self) -> int:
        return self.collection.count_documents({
            "$or": [
                {"is_attack": True},
                {"is_attack": "TRUE"},
                {"attack_type": {"$exists": True, "$ne": "normal"}},
            ]
        })

    def distinct_devices(self) -> List[str]:
        return sorted(str(value) for value in self.collection.distinct("device_id") if value)


class ResponseRepository:
    def __init__(self):
        settings = get_settings()
        db = get_database()
        self.collection = db[settings.response_collection]

    def insert_one(self, document: Dict[str, Any]):
        return self.collection.insert_one(document)

    def latest(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self.collection.find().sort("_id", -1).limit(limit))

    def find_by_actions(self, actions: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.collection.find({"action": {"$in": actions}}).sort("_id", -1).limit(limit))

    def count(self) -> int:
        return self.collection.count_documents({})


class PredictionRepository:
    def __init__(self):
        settings = get_settings()
        db = get_database()
        self.collection = db[settings.prediction_collection]

    def insert_one(self, document: Dict[str, Any]):
        return self.collection.insert_one(document)

    def latest(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self.collection.find().sort("created_at", -1).limit(limit))

    def priority_counts(self) -> Dict[str, int]:
        pipeline = [
            {"$match": {"priority": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": {"$toUpper": "$priority"}, "count": {"$sum": 1}}},
        ]
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for row in self.collection.aggregate(pipeline):
            priority = str(row.get("_id", "")).upper()
            if priority in counts:
                counts[priority] = int(row.get("count", 0))
        return counts


class DeviceStateRepository:
    def __init__(self):
        settings = get_settings()
        db = get_database()
        self.collection = db[settings.device_state_collection]

    def list_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(self.collection.find().sort("updated_at", -1).limit(limit))

    def get(self, device_id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"device_id": device_id})

    def upsert(
        self,
        device_id: str,
        state: str,
        action: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        device_type: str = "",
    ) -> Dict[str, Any]:
        document = {
            "device_id": device_id,
            "device_type": device_type,
            "state": state,
            "last_action": action,
            "reason": reason,
            "updated_at": utc_now_iso(),
            "metadata": metadata or {},
        }
        self.collection.update_one(
            {"device_id": device_id},
            {"$set": document, "$setOnInsert": {"created_at": document["updated_at"]}},
            upsert=True,
        )
        return document

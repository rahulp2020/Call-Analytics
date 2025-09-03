import os
import json
import aiofiles
import uuid
import random
from datetime import datetime
from abc import ABC


class Data(ABC):
    _filename = "data.json"

    @classmethod
    def create_json(cls, data):
        return {
            "call_id": str(uuid.uuid4()),
            "agent_id": str(uuid.uuid4()),
            "customer_id": str(uuid.uuid4()),
            "language": "en",
            "start_time": datetime.utcnow().date().isoformat(),
            "duration_seconds": random.randint(60, 600),
            "transcript": {
                "customer": data.get("input", ""),
                "agent": data.get("output", "")
            }
        }

    @classmethod
    async def save_json(cls, record):
        if os.path.exists(cls._filename):
            async with aiofiles.open(cls._filename, "r") as f:
                content = await f.read()
                data = json.loads(content) if content else []
        else:
            data = []

        data.append(record)

        async with aiofiles.open(cls._filename, "w") as f:
            await f.write(json.dumps(data, indent=2))

from abc import ABC, abstractmethod

import aiohttp, asyncio


class Transcripts(ABC):
    @abstractmethod
    def validate_response(self, response):
        pass

    @abstractmethod
    def load(self, session: aiohttp.ClientSession, offset: int):
        pass


class HuggingFaceTranscript(Transcripts):
    def __init__(self):
        self._base_url = "https://datasets-server.huggingface.co/rows"
        self._dataset = "MohammadOthman/mo-customer-support-tweets-945k"
        self._config = "default"
        self._split = "train"
        self._rows = 100
        self.limit = 10
        self.rate_limit = asyncio.Semaphore(3)

    def _create_offset(self, offset) -> list:
        offset_list = []
        max_fetch = self._rows // self.limit
        for i in range(max_fetch):
            offset_list.append(offset)
            offset = offset + self.limit

        return offset_list

    def validate_response(self, response):
        if not isinstance(response, dict):
            return False

        if "rows" not in response or not isinstance(response["rows"], list):
            return False

        for item in response["rows"]:
            if not isinstance(item, dict) or "row" not in item:
                return False
            row = item["row"]
            if not isinstance(row, dict):
                return False
            if "input" not in row or "output" not in row:
                return False
            if not isinstance(row["input"], str) or not isinstance(row["output"], str):
                return False
        return True

    async def _load(self, session: aiohttp.ClientSession, offset: int) -> dict:
        query_params = {
            "dataset": self._dataset,
            "config": self._config,
            "split": self._split,
            "offset": offset,
            "limit": self.limit
        }

        async with session.get(self._base_url, params=query_params) as response:
            if response.status == 200:
                data = await response.json()
                if not self.validate_response(data):
                    raise Exception("Invalid response structure")
                return data
            else:
                print(f"Failed to fetch data: {response.status}")
                response.raise_for_status()

    async def load(self, session: aiohttp.ClientSession, offset: int):
        offset_list = self._create_offset(offset)
        task = [self._load(session, off) for off in offset_list]
        async with self.rate_limit:
            result = await asyncio.gather(*task, return_exceptions=True)
            return result

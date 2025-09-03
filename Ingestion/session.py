import asyncio

import aiohttp


class SessionManager:
    _instance = None

    def __init__(self):
        if SessionManager._instance is not None:
            raise Exception("Session Manager already created!")

        self._timeout = aiohttp.ClientTimeout(total=10)
        self._Session = aiohttp.ClientSession(timeout=self._timeout)

    @staticmethod
    def get_instance():
        if SessionManager._instance is None:
            SessionManager._instance = SessionManager()
        return SessionManager._instance

    def get_session(self) -> aiohttp.ClientSession:
        return self._Session

    def is_closed(self) -> bool:
        return self._Session.closed

    async def close_session(self):
        await self._Session.close()

    def get_timeout(self) -> aiohttp.ClientTimeout:
        return self._timeout


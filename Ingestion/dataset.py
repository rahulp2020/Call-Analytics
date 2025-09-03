from typing import Dict, List, Optional
from Ingestion.session import SessionManager
from Ingestion.transcript import Transcripts, HuggingFaceTranscript
from Ingestion.data import Data


class Dataset:
    _instance = None

    def __init__(self):
        if Dataset._instance is not None:
            raise Exception("This class is a singleton!")

        self.response_traker: Dict[str, dict] = {}
        self.transcript: Transcripts = HuggingFaceTranscript()
        self.session_manager: SessionManager = SessionManager.get_instance()
        self.offset: int = 1
        self.data_list = []

    @staticmethod
    def get_instance():
        if Dataset._instance is None:
            Dataset._instance = Dataset()
        return Dataset._instance

    async def start_loading(self):
        try:

            if self.session_manager.is_closed():
                self.session_manager: SessionManager = SessionManager.get_instance()

            session = self.session_manager.get_session()
            responses = await self.transcript.load(session, self.offset)
            for response in responses:
                if isinstance(response, Exception):
                    print(f"Error occurred: {response}")
                else:
                    for item in response.get("rows", []):
                        data_to_persist = Data.create_json(item["row"])
                        self.data_list.append(data_to_persist)
                        await Data.save_json(data_to_persist)

            if not self.session_manager.is_closed():
                await self.session_manager.close_session()

            return self.data_list
        except Exception as e:
            raise Exception(f"Error in start_loading: {e}")











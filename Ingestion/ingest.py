import asyncio
from Ingestion.dataset import Dataset


async def main():
    dataset = Dataset.get_instance()
    return await dataset.start_loading()


# if __name__ == "__main__":
#     asyncio.run(main())

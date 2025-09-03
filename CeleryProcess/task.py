import asyncio

from celery.signals import worker_ready

from CeleryProcess.celery_app import celery_app
from typing import Dict, Any
from Ingestion.ingest import main as ingestion_main
from InsightProcessor.ai import AIProcessor



@worker_ready.connect
def at_start(sender, **kwargs):
    with sender.app.connection() as conn:
        sender.app.send_task("tasks.process_ingestion", connection=conn)
        print("Initial ingestion triggered at worker startup")


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3, name="tasks.process_ingestion")
def process_ingestion(self):
    print("Starting ingestion process...")

    items = asyncio.run(ingestion_main())
    print(f"Ingestion process completed. {len(items)} items ingested.")

    for item in items:
        print(f"Ingested item: pushing to AI processing queue")
        ai_processing_task.delay(item)

    print("All ingestion items queued for AI processing.")
    return {"status": "ok", "items_count": len(items)}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3, name="tasks.ai_processing_task")
def ai_processing_task(self, item_data: Dict[Any, Any]):
    print("Starting AI processing task...")

    ai_processor = AIProcessor()
    processed_data = ai_processor.process_call_data(item_data)

    print("AI processing task completed.")
    return {"status": "ok", "call_id": item_data.get("call_id")}

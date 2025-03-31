import os
from fastapi import FastAPI
from dotenv import load_dotenv
import asyncio
import logging

from app.api.webhook import router as webhook_router
from app.services.message_queue import start_worker_pool

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp E-Commerce Bot")

app.include_router(webhook_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Start the worker pool when the app starts up"""
    # Get the number of workers from environment or use default
    worker_count = int(os.getenv("MESSAGE_WORKER_COUNT", "3"))
    logger.info(f"Starting message worker pool with {worker_count} workers")

    # Start the worker pool in a background task
    asyncio.create_task(start_worker_pool(worker_count))
    logger.info("Message worker pool started successfully")

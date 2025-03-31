import os
import json
from typing import Dict, Any, List, Optional, Union, Callable
import uuid
import logging
import asyncio
import threading
from queue import Queue
from datetime import datetime
from asyncio import Task, create_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreadSafeQueue:
    """Thread-safe in-memory message queue with async worker support"""

    def __init__(self):
        self.queue = Queue()
        self._lock = threading.RLock()
        self._event = asyncio.Event()
        self._workers: List[Task] = []
        self._shutting_down = False

    async def enqueue(self, message: Dict[str, Any]) -> None:
        """Add a message to the queue in a thread-safe manner"""
        with self._lock:
            self.queue.put(message)
            self._event.set()  # Signal that a new message is available

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Remove and return a message from the queue in a thread-safe manner"""
        # Wait for a message to be available
        if self.queue.empty():
            self._event.clear()
            try:
                # Wait for a message with a timeout
                await asyncio.wait_for(self._event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                return None

        # Get a message from the queue with the lock
        with self._lock:
            if not self.queue.empty():
                return self.queue.get()
            return None

    async def get_length(self) -> int:
        """Get the current queue length in a thread-safe manner"""
        with self._lock:
            return self.queue.qsize()

    async def peek(self) -> Optional[Dict[str, Any]]:
        """View the next message without removing it"""
        with self._lock:
            if not self.queue.empty():
                # This is not truly a peek since we can't peek at Queue, but we'll reinsert it
                message = self.queue.get()
                self.queue.put(message)  # Put it back
                return message
            return None

    async def register_worker(
        self, worker_func: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """Register an async worker function to process messages"""
        worker_task = create_task(self._worker_loop(worker_func))
        self._workers.append(worker_task)
        logger.info(f"Registered worker task {id(worker_task)}")

    async def _worker_loop(self, worker_func: Callable[[Dict[str, Any]], Any]) -> None:
        """Internal async worker loop that processes messages from the queue"""
        worker_id = id(asyncio.current_task())
        logger.info(f"Async worker {worker_id} started")

        while not self._shutting_down:
            try:
                message = await self.dequeue()
                if message:
                    # Process message with the worker function
                    await self._safe_process_message(worker_func, message)
                else:
                    # No message available, just wait a bit to avoid CPU spinning
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {str(e)}")
                await asyncio.sleep(1)  # Avoid tight loop in case of persistent errors

        logger.info(f"Worker {worker_id} shutting down")

    async def _safe_process_message(
        self, worker_func: Callable[[Dict[str, Any]], Any], message: Dict[str, Any]
    ) -> None:
        """Safely process a message with error handling"""
        try:
            worker_id = id(asyncio.current_task())
            logger.info(
                f"Processing message: {message.get('id')} in worker {worker_id}"
            )
            await worker_func(message)
            logger.info(f"Successfully processed message: {message.get('id')}")
        except Exception as e:
            logger.error(f"Error processing message {message.get('id')}: {str(e)}")

    async def shutdown(self) -> None:
        """Gracefully shutdown all worker tasks"""
        logger.info("Shutting down queue and worker tasks...")
        self._shutting_down = True

        # Cancel all worker tasks
        for worker in self._workers:
            if not worker.done():
                worker.cancel()

        # Wait for all tasks to complete
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)


# For simplicity, we'll use a thread-safe in-memory queue for now
# In production, this would be replaced with Redis or another distributed queue
message_queue = ThreadSafeQueue()


async def prepare_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a message by adding required fields"""
    # Add a unique ID if not present
    if "id" not in message:
        message["id"] = str(uuid.uuid4())

    # Add timestamp if not present
    if "timestamp" not in message:
        message["timestamp"] = datetime.now().isoformat()

    # Ensure message_type is set
    if "message_type" not in message:
        message["message_type"] = "media" if message.get("media_url") else "text"

    # Ensure metadata exists
    if "metadata" not in message:
        message["metadata"] = {}

    return message


async def enqueue_message(message: Dict[str, Any]) -> None:
    """Add a message to the processing queue"""
    prepared_message = await prepare_message(message)
    await message_queue.enqueue(prepared_message)


async def process_messages() -> None:
    """Legacy message processor - starts a single worker"""
    from app.services.message_processor import process_message

    await message_queue.register_worker(process_message)


async def process_message_worker(message: Dict[str, Any]) -> None:
    """Worker function that processes a single message"""
    from app.services.message_processor import process_message

    await process_message(message)


async def start_worker_pool(num_workers: int = 3) -> None:
    """Start a pool of async workers to process messages"""
    logger.info(f"Starting worker pool with {num_workers} workers")

    # Register the specified number of workers
    for i in range(num_workers):
        await message_queue.register_worker(process_message_worker)

    logger.info("Worker pool started successfully")

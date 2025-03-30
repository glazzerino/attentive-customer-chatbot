import os
import json
from typing import Dict, Any, List
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InMemoryQueue:
    """Simple in-memory message queue for development"""
    
    def __init__(self):
        self.queue = []
    
    async def enqueue(self, message: Dict[str, Any]) -> None:
        """Add a message to the queue"""
        self.queue.append(message)
    
    async def dequeue(self) -> Dict[str, Any]:
        """Remove and return a message from the queue"""
        if not self.queue:
            return None
        return self.queue.pop(0)
    
    async def get_length(self) -> int:
        """Get the current queue length"""
        return len(self.queue)

# For simplicity, we'll use an in-memory queue for now
# In production, this would be replaced with Redis
message_queue = InMemoryQueue()

async def enqueue_message(message: Dict[str, Any]) -> None:
    """Add a message to the processing queue"""
    # Add a unique ID if not present
    if 'id' not in message:
        message['id'] = str(uuid.uuid4())
    
    await message_queue.enqueue(message)

async def process_messages() -> None:
    """Process messages from the queue"""
    from app.services.message_processor import process_message
    
    while True:
        # Get a message from the queue
        message = await message_queue.dequeue()
        
        if message:
            logger.info(f"received message: {message}")
            await process_message(message)

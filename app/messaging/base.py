from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class MessagingPlatform(ABC):
    """Base interface for messaging platform adapters."""
    
    @abstractmethod
    async def validate_webhook(self, request_data: Dict[str, Any]) -> bool:
        """Validate incoming webhook request"""
        pass
    
    @abstractmethod
    async def parse_message(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse incoming message into standardized format"""
        pass
    
    @abstractmethod
    async def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send text message to user"""
        pass
    
    @abstractmethod
    async def send_media(self, phone_number: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send media message to user"""
        pass

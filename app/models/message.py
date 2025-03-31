import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

from app.models.database import database
from app.models.conversation import Conversation


class Message:
    """Message model representing a single message in a conversation"""

    def __init__(
        self,
        id: str,
        conversation_id: str,
        role: str,
        content: str,
        phone_number: Optional[str] = None,
        media_url: Optional[str] = None,
        message_type: str = "text",
        platform: str = "whatsapp",
        metadata: Optional[Dict[str, Any]] = None,
        raw_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.id = id
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.phone_number = phone_number
        self.media_url = media_url
        self.message_type = message_type
        self.platform = platform
        self.metadata = metadata or {}
        self.raw_data = raw_data or {}
        self.timestamp = timestamp or datetime.now()

    @classmethod
    async def create(
        cls,
        conversation_id: str,
        role: str,
        content: str,
        phone_number: Optional[str] = None,
        media_url: Optional[str] = None,
        message_type: str = "text",
        platform: str = "whatsapp",
        metadata: Optional[Dict[str, Any]] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> "Message":
        """Create a new message"""
        conn = database.get_connection()
        cursor = conn.cursor()

        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})
        raw_data_json = json.dumps(raw_data or {})

        cursor.execute(
            """INSERT INTO messages 
			   (id, conversation_id, role, content, phone_number, media_url, message_type, 
				platform, metadata, raw_data, timestamp)
			   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message_id,
                conversation_id,
                role,
                content,
                phone_number,
                media_url,
                message_type,
                platform,
                metadata_json,
                raw_data_json,
                now,
            ),
        )

        # Update conversation last updated time
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )

        conn.commit()

        return Message(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            phone_number=phone_number,
            media_url=media_url,
            message_type=message_type,
            platform=platform,
            metadata=metadata or {},
            raw_data=raw_data or {},
            timestamp=datetime.fromisoformat(now),
        )

    @classmethod
    async def get_by_id(cls, message_id: str) -> Optional["Message"]:
        """Get a message by ID"""
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))

        message_data = cursor.fetchone()
        if not message_data:
            return None

        metadata = {}
        raw_data = {}

        try:
            if 'metadata' in message_data and message_data['metadata']:
                metadata = json.loads(message_data['metadata'])
            if 'raw_data' in message_data and message_data['raw_data']:
                raw_data = json.loads(message_data['raw_data'])
        except json.JSONDecodeError:
            pass

        return Message(
            id=message_data['id'],
            conversation_id=message_data['conversation_id'],
            role=message_data['role'],
            content=message_data['content'],
            phone_number=message_data['phone_number'] if 'phone_number' in message_data else None,
            media_url=message_data['media_url'] if 'media_url' in message_data else None,
            message_type=message_data['message_type'] if 'message_type' in message_data else 'text',
            platform=message_data['platform'] if 'platform' in message_data else 'whatsapp',
            metadata=metadata,
            raw_data=raw_data,
            timestamp=datetime.fromisoformat(message_data['timestamp']),
        )

    @classmethod
    async def get_messages_for_conversation(
        cls, conversation_id: str, limit: int = 10
    ) -> List["Message"]:
        """Get recent messages from a conversation"""
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?",
            (conversation_id, limit),
        )

        messages = []
        for row in cursor.fetchall():
            metadata = {}
            raw_data = {}

            try:
                if 'metadata' in row and row['metadata']:
                    metadata = json.loads(row['metadata'])
                if 'raw_data' in row and row['raw_data']:
                    raw_data = json.loads(row['raw_data'])
            except json.JSONDecodeError:
                pass

            messages.append(
                Message(
                    id=row['id'],
                    conversation_id=row['conversation_id'],
                    role=row['role'],
                    content=row['content'],
                    phone_number=row['phone_number'] if 'phone_number' in row else None,
                    media_url=row['media_url'] if 'media_url' in row else None,
                    message_type=row['message_type'] if 'message_type' in row else 'text',
                    platform=row['platform'] if 'platform' in row else 'whatsapp',
                    metadata=metadata,
                    raw_data=raw_data,
                    timestamp=datetime.fromisoformat(row['timestamp']),
                )
            )

        # Return messages in chronological order
        return list(reversed(messages))

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "phone_number": self.phone_number,
            "media_url": self.media_url,
            "message_type": self.message_type,
            "platform": self.platform,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    async def from_webhook_data(
        cls, data: Dict[str, Any], conversation_id: str
    ) -> "Message":
        """Create a message from standardized webhook data"""
        return await cls.create(
            conversation_id=conversation_id,
            role="user",
            content=data.get("content", ""),
            phone_number=data.get("phone_number"),
            media_url=data.get("media_url"),
            message_type="text" if not data.get("media_url") else "media",
            platform=data.get("platform", "whatsapp"),
            metadata={"message_id": data.get("message_id")},
            raw_data=data.get("raw_data", {}),
        )


import json  # Needed for JSON serialization/deserialization

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.models.database import database
from app.models.user import User

class Conversation:
    """Conversation model representing a chat session"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        context: Optional[str] = None,
        active_product_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.context = context or "{}"
        self.active_product_id = active_product_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @classmethod
    async def create(cls, user_id: str) -> 'Conversation':
        """Create a new conversation"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        conversation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO conversations (id, user_id, context, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, user_id, "{}", now, now)
        )
        
        conn.commit()
        
        # Update user's active conversation
        user = await User.get_by_phone(user_id)
        if user:
            await user.update_active_conversation(conversation_id)
        
        return Conversation(
            id=conversation_id,
            user_id=user_id,
            context="{}",
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )
    
    @classmethod
    async def get_by_id(cls, conversation_id: str) -> Optional['Conversation']:
        """Get a conversation by ID"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        
        conversation_data = cursor.fetchone()
        if not conversation_data:
            return None
        
        return Conversation(
            id=conversation_data['id'],
            user_id=conversation_data['user_id'],
            context=conversation_data['context'],
            active_product_id=conversation_data['active_product_id'],
            created_at=datetime.fromisoformat(conversation_data['created_at']),
            updated_at=datetime.fromisoformat(conversation_data['updated_at'])
        )
    
    @classmethod
    async def get_active_for_user(cls, user_id: str) -> Optional['Conversation']:
        """Get the active conversation for a user"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT active_conversation_id FROM users WHERE phone_number = ?",
            (user_id,)
        )
        
        result = cursor.fetchone()
        if not result or not result['active_conversation_id']:
            return None
        
        return await cls.get_by_id(result['active_conversation_id'])
    
    async def update(self) -> None:
        """Update the conversation in the database"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        self.updated_at = datetime.fromisoformat(now)
        
        cursor.execute(
            "UPDATE conversations SET context = ?, active_product_id = ?, updated_at = ? WHERE id = ?",
            (self.context, self.active_product_id, now, self.id)
        )
        
        conn.commit()
    
    async def add_message(self, role: str, content: str) -> str:
        """Add a message to the conversation"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO messages (id, conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (message_id, self.id, role, content, now)
        )
        
        # Update conversation last updated time
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, self.id)
        )
        
        self.updated_at = datetime.fromisoformat(now)
        conn.commit()
        
        return message_id
    
    async def get_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from the conversation"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?",
            (self.id, limit)
        )
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row['id'],
                'role': row['role'],
                'content': row['content'],
                'timestamp': row['timestamp']
            })
        
        # Return messages in chronological order
        return list(reversed(messages))

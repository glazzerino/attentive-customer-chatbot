import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from app.models.database import database

class User:
    """User model representing a customer"""
    
    def __init__(
        self,
        phone_number: str,
        name: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_interaction: Optional[datetime] = None,
        active_conversation_id: Optional[str] = None
    ):
        self.phone_number = phone_number
        self.name = name
        self.created_at = created_at or datetime.now()
        self.last_interaction = last_interaction or datetime.now()
        self.active_conversation_id = active_conversation_id
    
    @classmethod
    async def get_by_phone(cls, phone_number: str) -> Optional['User']:
        """Get a user by phone number"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM users WHERE phone_number = ?",
            (phone_number,)
        )
        
        user_data = cursor.fetchone()
        if not user_data:
            return None
        
        return User(
            phone_number=user_data['phone_number'],
            name=user_data['name'],
            created_at=datetime.fromisoformat(user_data['created_at']),
            last_interaction=datetime.fromisoformat(user_data['last_interaction']),
            active_conversation_id=user_data['active_conversation_id']
        )
    
    @classmethod
    async def create_or_update(cls, phone_number: str, name: Optional[str] = None) -> 'User':
        """Create a new user or update an existing one"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        user = await cls.get_by_phone(phone_number)
        now = datetime.now().isoformat()
        
        if user:
            # Update existing user
            cursor.execute(
                "UPDATE users SET last_interaction = ?, name = COALESCE(?, name) WHERE phone_number = ?",
                (now, name, phone_number)
            )
            user.last_interaction = datetime.fromisoformat(now)
            if name:
                user.name = name
        else:
            # Create new user
            cursor.execute(
                "INSERT INTO users (phone_number, name, last_interaction) VALUES (?, ?, ?)",
                (phone_number, name, now)
            )
            user = User(
                phone_number=phone_number,
                name=name,
                last_interaction=datetime.fromisoformat(now)
            )
        
        conn.commit()
        return user
    
    async def update_active_conversation(self, conversation_id: str) -> None:
        """Update the user's active conversation ID"""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET active_conversation_id = ? WHERE phone_number = ?",
            (conversation_id, self.phone_number)
        )
        
        self.active_conversation_id = conversation_id
        conn.commit()

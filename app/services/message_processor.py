import json
from typing import Dict, Any, List, Optional, Union

from anthropic import Anthropic

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.llm_client import AnthropicClient
from app.messaging.twilio_adapter import TwilioWhatsAppAdapter

# Initialize the LLM client and messaging adapter
llm_client = AnthropicClient()
twilio_adapter = TwilioWhatsAppAdapter()


async def process_message(message_data: Dict[str, Any]) -> None:
    """Process an incoming message from the queue"""
    # Extract user information
    phone_number = message_data.get("phone_number")
    content = message_data.get("content", "")

    if not phone_number or not content:
        return

    # Get or create user
    user = await User.create_or_update(phone_number)

    # Get active conversation or create a new one
    conversation = await Conversation.get_active_for_user(phone_number)
    if not conversation:
        conversation = await Conversation.create(phone_number)

    # Add user message to conversation using enhanced Message model
    await conversation.add_message(
        role="user",
        content=content,
        phone_number=phone_number,
        media_url=message_data.get("media_url"),
        message_type=message_data.get("message_type", "text"),
        platform=message_data.get("platform", "whatsapp"),
        metadata=message_data.get("metadata", {}),
        raw_data=message_data.get("raw_data", {}),
    )

    # Get recent conversation messages for context
    messages = await conversation.get_messages()

    # Generate response using LLM
    response = await llm_client.generate_response(messages, conversation.context)

    # Add assistant message to conversation
    await conversation.add_message(
        role="assistant",
        content=response["content"],
        phone_number=None,
        message_type="text",
        platform="system",
    )

    # Check for function calls and execute them
    if "function_calls" in response:
        # Process function calls here
        # For now this is just a placeholder
        pass

    # Update conversation context if needed
    if response.get("updated_context"):
        conversation.context = json.dumps(response["updated_context"])
        await conversation.update()

    # Send response back to user
    await twilio_adapter.send_message(phone_number, response["content"])

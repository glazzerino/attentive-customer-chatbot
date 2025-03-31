from fastapi import APIRouter, Request, Response, Header, HTTPException, Depends
from typing import Optional, Dict, Any

from app.messaging.twilio_adapter import TwilioWhatsAppAdapter
from app.services.message_queue import enqueue_message
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter(prefix="/webhook")

# Initialize the messaging platform adapter
twilio_adapter = TwilioWhatsAppAdapter()


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request, x_twilio_signature: Optional[str] = Header(None)
):
    """Webhook endpoint for Twilio WhatsApp"""
    # Get request data
    form_data = await request.form()
    request_data = dict(form_data)
    # Get full URL for validation
    url = str(request.url)

    # Validate webhook signature - note we're passing url separately
    if not await twilio_adapter.validate_webhook(url, request_data, x_twilio_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse incoming message
    message = await twilio_adapter.parse_message(request_data)

    # Enqueue message for processing
    await enqueue_message(message)

    # Return TwiML response
    return Response(content="<Response></Response>", media_type="application/xml")


@router.post("/{platform}")
async def generic_webhook(platform: str, request: Request):
    """Generic webhook endpoint for other messaging platforms"""
    # This is a placeholder for future platform integrations
    return {
        "message": f"Received webhook for {platform}, but no handler is implemented yet."
    }

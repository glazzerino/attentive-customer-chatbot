from typing import Dict, Any, Optional
from dotenv import dotenv_values

from twilio.rest import Client
from twilio.request_validator import RequestValidator

from app.messaging.base import MessagingPlatform


class TwilioWhatsAppAdapter(MessagingPlatform):
    """Twilio WhatsApp messaging platform adapter."""

    def __init__(self):
        config = dotenv_values()
        self.account_sid = config.get("TWILIO_ACCOUNT_SID")
        self.auth_token = config.get("TWILIO_AUTH_TOKEN")
        self.from_number = config.get("TWILIO_PHONE_NUMBER")

        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError(
                "Twilio credentials not properly configured. Check environment variables."
            )

        self.client = Client(self.account_sid, self.auth_token)
        self.validator = RequestValidator(self.auth_token)

    async def validate_webhook(
        self, request_data: Dict[str, Any], signature: Optional[str]
    ) -> bool:
        """Validate incoming webhook request signature"""
        # Get the URL from the request data or use a default
        url = request_data.get("url", "")
        return self.validator.validate(url, request_data, signature)

    async def parse_message(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Twilio WhatsApp message into standardized format"""
        standardized_message = {
            "platform": "whatsapp",
            "phone_number": request_data.get("From", "").replace("whatsapp:", ""),
            "message_id": request_data.get("MessageSid", ""),
            "content": request_data.get("Body", ""),
            "media_url": request_data.get("MediaUrl0", None),
            "message_type": "media" if request_data.get("MediaUrl0") else "text",
            "timestamp": request_data.get("timestamp", ""),
            "metadata": {"message_sid": request_data.get("MessageSid", "")},
            "raw_data": request_data,
        }

        return standardized_message

    async def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send text message to user via Twilio WhatsApp"""
        whatsapp_phone = f"whatsapp:{phone_number}"
        whatsapp_from = f"whatsapp:{self.from_number}"

        message_response = self.client.messages.create(
            body=message, from_=whatsapp_from, to=whatsapp_phone
        )

        return {"message_id": message_response.sid, "status": message_response.status}

    async def send_media(
        self, phone_number: str, media_url: str, caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send media message to user via Twilio WhatsApp"""
        whatsapp_phone = f"whatsapp:{phone_number}"
        whatsapp_from = f"whatsapp:{self.from_number}"

        message_response = self.client.messages.create(
            media_url=[media_url], body=caption, from_=whatsapp_from, to=whatsapp_phone
        )

        return {"message_id": message_response.sid, "status": message_response.status}

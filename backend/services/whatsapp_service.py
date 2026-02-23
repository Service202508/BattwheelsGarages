"""
WhatsApp Business API Service
==============================

Handles sending messages via WhatsApp Business Cloud API (Meta Graph API v18.0).

Supported message types:
  - Text messages
  - Document messages (e.g., PDF invoices)
  - Template messages (pre-approved by Meta)

Phone number formatting:
  - Strip non-digits
  - If starts with 0 → replace with 91
  - If doesn't start with 91 → prepend 91

Credentials stored via credential_service (encrypted at rest):
  - phone_number_id: Meta Business Phone Number ID
  - access_token: Permanent System User Token
"""

import httpx
import logging
from typing import List, Optional

from services.credential_service import get_credentials, WHATSAPP

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v18.0"


class WhatsAppNotConfigured(Exception):
    """Raised when org has no WhatsApp credentials configured."""
    pass


class WhatsAppError(Exception):
    """Raised when the Meta API returns an error."""
    pass


def format_phone(phone: str) -> str:
    """
    Normalize a phone number to E.164 format for India.
      09876543210   → 919876543210
      9876543210    → 919876543210
      +919876543210 → 919876543210
    """
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("0"):
        digits = "91" + digits[1:]
    if not digits.startswith("91"):
        digits = "91" + digits
    return digits


async def _get_creds(org_id: str) -> dict:
    creds = await get_credentials(org_id, WHATSAPP)
    if not creds or not creds.get("phone_number_id") or not creds.get("access_token"):
        raise WhatsAppNotConfigured(
            f"WhatsApp Business API not configured for org {org_id}. "
            "Add Phone Number ID and Access Token in Settings → Integrations."
        )
    return creds


async def send_whatsapp_text(to_phone: str, message: str, org_id: str) -> dict:
    """Send a plain text WhatsApp message."""
    creds = await _get_creds(org_id)
    to = format_phone(to_phone)
    url = f"{GRAPH_API_BASE}/{creds['phone_number_id']}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    return await _post(url, payload, creds["access_token"])


async def send_whatsapp_document(
    to_phone: str,
    document_url: str,
    filename: str,
    caption: str,
    org_id: str,
) -> dict:
    """Send a document (e.g., PDF invoice) via WhatsApp."""
    creds = await _get_creds(org_id)
    to = format_phone(to_phone)
    url = f"{GRAPH_API_BASE}/{creds['phone_number_id']}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "link": document_url,
            "filename": filename,
            "caption": caption,
        },
    }
    return await _post(url, payload, creds["access_token"])


async def send_whatsapp_template(
    to_phone: str,
    template_name: str,
    params: List[str],
    org_id: str,
    language: str = "en",
) -> dict:
    """Send a pre-approved WhatsApp template message."""
    creds = await _get_creds(org_id)
    to = format_phone(to_phone)
    url = f"{GRAPH_API_BASE}/{creds['phone_number_id']}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in params],
                }
            ],
        },
    }
    return await _post(url, payload, creds["access_token"])


async def _post(url: str, payload: dict, access_token: str) -> dict:
    """Execute the Graph API POST request."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code not in (200, 201):
        error_body = response.text[:500]
        logger.error(f"WhatsApp API error {response.status_code}: {error_body}")
        raise WhatsAppError(
            f"WhatsApp API returned {response.status_code}: {error_body}"
        )

    data = response.json()
    messages = data.get("messages", [])
    message_id = messages[0].get("id") if messages else None
    logger.info(f"WhatsApp message sent. message_id={message_id}")
    return {"message_id": message_id, "status": "sent"}

import re
from typing import Any, Dict, Optional
from urllib.parse import quote
from app.schemas.lead import Lead
from app.schemas.outreach import Outreach


def prepare_whatsapp_url(phone: Optional[str], message: Optional[str] = None) -> Optional[str]:
    """
    Safely prepares a WhatsApp click-to-chat destination URL (wa.me) from a phone number.
    Does NOT call any external WhatsApp APIs or send messages.
    Returns None if phone is invalid or has fewer than 7 digits.
    """
    if not phone:
        return None

    raw = phone.strip()
    digits = re.sub(r"\D", "", raw)
    if not digits or len(digits) < 7:
        return None

    base_url = f"https://wa.me/{digits}"
    if message and message.strip():
        encoded_msg = quote(message.strip())
        return f"{base_url}?text={encoded_msg}"

    return base_url


def prepare_email_action_data(lead: Lead, outreach: Optional[Outreach] = None) -> Dict[str, Any]:
    """
    Exposes email action draft data for frontend review.
    Does NOT call any email APIs or send emails.
    """
    email_addr = lead.contact.email if lead.contact else None
    return {
        "email": email_addr,
        "subject": outreach.subject if outreach else None,
        "body": outreach.message if outreach else None,
        "outreach_id": str(outreach.id) if outreach and outreach.id else None,
        "status": outreach.status if outreach else None,
        "is_available": bool(email_addr and outreach),
    }

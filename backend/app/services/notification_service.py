"""
Push notification service using Firebase Cloud Messaging (FCM).

Falls back gracefully if Firebase credentials are not configured.
"""
import asyncio
import base64
import json
import os
import tempfile
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_firebase_initialised = False


def _init_firebase() -> bool:
    """Lazy-initialise Firebase Admin SDK. Returns True if ready."""
    global _firebase_initialised
    if _firebase_initialised:
        return True

    creds_b64 = settings.FIREBASE_CREDENTIALS_BASE64
    if not creds_b64:
        logger.warning("notifications.firebase_not_configured")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        creds_json = base64.b64decode(creds_b64).decode("utf-8")
        creds_dict = json.loads(creds_json)

        # Write to a temp file — firebase_admin requires a file path or dict
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(creds_dict, f)
            tmp_path = f.name

        cred = credentials.Certificate(tmp_path)
        firebase_admin.initialize_app(cred)
        os.unlink(tmp_path)
        _firebase_initialised = True
        logger.info("notifications.firebase_ready")
        return True
    except Exception as e:
        logger.error("notifications.firebase_init_failed", error=str(e))
        return False


async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """
    Send a push notification to a specific device token.

    Runs Firebase in a thread pool so it doesn't block the event loop.
    Returns True on success, False on failure.
    """
    if not _init_firebase():
        logger.debug("notifications.skipped_no_firebase", title=title)
        return False

    try:
        import firebase_admin
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    click_action="FLUTTER_NOTIFICATION_CLICK",
                ),
            ),
        )

        # Send in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: messaging.send(message)
        )
        logger.info("notifications.sent", title=title, message_id=response)
        return True

    except Exception as e:
        logger.error("notifications.send_failed", title=title, error=str(e))
        return False


async def send_bulk_notification(
    tokens: list[str],
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> int:
    """Send the same notification to multiple device tokens. Returns success count."""
    tasks = [send_push_notification(t, title, body, data) for t in tokens]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(1 for r in results if r is True)

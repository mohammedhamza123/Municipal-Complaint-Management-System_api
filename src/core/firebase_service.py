"""
Firebase Cloud Messaging Service
Handles sending push notifications via FCM
"""
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Try to initialize Firebase Admin SDK
_firebase_initialized = False

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    from src.core.config import settings

    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
    else:
        logger.warning(
            f"Firebase credentials file not found at '{cred_path}'. "
            "Push notifications will be disabled. "
            "Place your service account JSON file there to enable FCM."
        )
except ImportError:
    logger.warning("firebase-admin package not installed. Push notifications disabled.")
except Exception as e:
    logger.warning(f"Failed to initialize Firebase: {e}")


def is_firebase_available() -> bool:
    """Check if Firebase is initialized and ready"""
    return _firebase_initialized


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """
    Send a push notification to a single device.
    
    Args:
        token: FCM device token
        title: Notification title
        body: Notification body
        data: Optional data payload
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not _firebase_initialized:
        logger.debug("Firebase not initialized, skipping push notification")
        return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    channel_id="municipal_notifications",
                ),
            ),
        )
        response = messaging.send(message)
        logger.info(f"Push notification sent: {response}")
        return True
    except messaging.UnregisteredError:
        logger.warning(f"FCM token is no longer valid: {token[:20]}...")
        return False
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False


def send_push_to_multiple(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> int:
    """
    Send push notification to multiple devices.
    
    Returns:
        Number of successfully sent notifications
    """
    if not _firebase_initialized or not tokens:
        return 0

    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    channel_id="municipal_notifications",
                ),
            ),
        )
        response = messaging.send_each_for_multicast(message)
        logger.info(
            f"Push notifications sent: {response.success_count} success, "
            f"{response.failure_count} failures"
        )
        return response.success_count
    except Exception as e:
        logger.error(f"Failed to send multicast push: {e}")
        return 0


























from aiogram import Bot
from src.core.database.service import db_service
import logging

logger = logging.getLogger(__name__)

async def send_log(bot: Bot, message: str, log_type: str = "errors"):
    """
    Sends a log message to the configured administrative chat/thread.
    log_type: "errors" or "feedback"
    """
    try:
        log_cfg = await db_service.get_system_setting("log_settings")
        # Retrieve destination configuration safely
        dest = log_cfg.get("destination") or {}
        if not isinstance(dest, dict):
            dest = {}
        enabled = log_cfg.get("enabled_types", ["errors", "feedback"])
        # Abort if destination not set or log type disabled
        if not dest or log_type not in enabled:
            return
        # Extract IDs and ensure they are integers when present
        chat_id = dest.get("chat_id")
        thread_id = dest.get("thread_id")
        try:
            chat_id = int(chat_id) if chat_id is not None else None
            thread_id = int(thread_id) if thread_id is not None else None
        except (ValueError, TypeError):
            logger.error("Invalid chat_id or thread_id in log settings")
            return
        if chat_id is None:
            logger.error("Log destination missing chat_id")
            return
        prefix = "🚨 <b>SYSTEM ERROR</b>" if log_type == "errors" else "💬 <b>FEEDBACK</b>"
        full_text = f"{prefix}\n\n{message}"
        # Send with retry logic
        for attempt in range(3):
            try:
                send_kwargs = {
                    "chat_id": chat_id,
                    "text": full_text,
                    "parse_mode": "HTML",
                }
                if thread_id is not None:
                    send_kwargs["message_thread_id"] = thread_id
                await bot.send_message(**send_kwargs)
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"❌ Send error: {e}")

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
        dest = log_cfg.get("destination")
        enabled = log_cfg.get("enabled_types", ["errors", "feedback"])
        
        if not dest or log_type not in enabled:
            return
            
        chat_id = dest.get("chat_id")
        thread_id = dest.get("thread_id")
        
        prefix = "🚨 <b>SYSTEM ERROR</b>" if log_type == "errors" else "💬 <b>FEEDBACK</b>"
        full_text = f"{prefix}\n\n{message}"
        
        await bot.send_message(
            chat_id=chat_id,
            text=full_text,
            message_thread_id=thread_id,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"CRITICAL: Failed to send log to admin chat: {e}")

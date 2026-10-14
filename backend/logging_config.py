import sys
import re
from loguru import logger


def sanitize_url(url: str) -> str:
    """Mask credentials in MongoDB connection strings to prevent log leakage."""
    if not url:
        return ""
    # Mask mongodb://user:pass@host or mongodb+srv://user:pass@host
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:******@", url)


def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )
    return logger

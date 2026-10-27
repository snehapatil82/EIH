import logging
import sys
from rich.logging import RichHandler
from app.core.config import settings

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True, show_path=False) if sys.stdout.isatty() else logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger("eih")

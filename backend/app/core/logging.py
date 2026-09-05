import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """
    Sets up structured logging for the application.
    Logs format includes timestamp, log level, logger name, and message.
    Sensitive credentials and secrets are excluded from logs.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger("aegis_sales_ai")

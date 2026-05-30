import logging
import sys


def setup_logging(level: str) -> None:
    """Configure process logging without exposing secrets."""
    normalized = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=normalized,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

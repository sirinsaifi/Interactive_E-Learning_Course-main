"""Health check service — verifies the database is reachable."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    def __init__(self, db: Session):
        self.db = db

    def check_database(self) -> bool:
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Database health check failed: %s", exc)
            return False

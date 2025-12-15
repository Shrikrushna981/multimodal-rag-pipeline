import logging
from pythonjsonlogger import jsonlogger
from app.core.config import get_settings
import sys

settings = get_settings()

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        # Avoid propagation to root logger to keep audit logs distinct if needed,
        # but for K8s usually stdout is fine. 
        self.logger.propagate = False
        
        handler = logging.StreamHandler(sys.stdout)
        # Structured JSON formatter for Audit
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s %(audit_type)s %(user_id)s %(session_id)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_query(self, session_id: str, query: str, user_id: str = "anonymous"):
        self.logger.info(
            "User Query",
            extra={
                "audit_type": "QUERY",
                "session_id": session_id,
                "user_id": user_id,
                "content_preview": query[:100] # Mask/truncate if PII concern, but audit usually needs full.
            }
        )

    def log_response(self, session_id: str, response: str, latency_ms: float):
        self.logger.info(
            "System Response",
            extra={
                "audit_type": "RESPONSE",
                "session_id": session_id,
                "latency_ms": latency_ms,
                "content_preview": response[:100]
            }
        )

# Singleton
audit_logger = AuditLogger()

"""
Audit logger — immutable, structured log of every write operation.

In production pipe this to a SIEM (Splunk, Datadog, ELK) or a separate
append-only audit log store. Here we write structured JSON to a dedicated
'audit' logger so it can be routed independently.
"""

import json
import logging
from datetime import datetime, timezone

# Route audit events to their own file/stream in production via logging config
audit_logger = logging.getLogger('books_api.audit')


class AuditLogger:
    def log(
        self,
        action: str,
        resource: str,
        status: int,
        ip: str,
        trace_id: str,
        user_id: str | None = None,
        extra: dict | None = None,
    ):
        record = {
            'timestamp':  datetime.now(timezone.utc).isoformat(),
            'event':      'audit',
            'action':     action,
            'resource':   resource,
            'status':     status,
            'ip':         ip,
            'trace_id':   trace_id,
            'user_id':    user_id or 'anonymous',
        }
        if extra:
            record.update(extra)

        # Log at INFO so it's captured; use a dedicated handler in production
        audit_logger.info(json.dumps(record))

"""
Web Application Firewall (WAF) middleware.

Protects against:
  - SQL injection
  - XSS (cross-site scripting)
  - Path traversal
  - Oversized payloads
  - Suspicious user-agents (scanners/bots)
  - Null byte injection
"""

import re
import logging
from flask import request, jsonify, g

logger = logging.getLogger('books_api.waf')

# ── Detection patterns ────────────────────────────────────────────────────────

_SQL_INJECTION = re.compile(
    r"(\b(select|insert|update|delete|drop|create|alter|exec|union|--|;)\b"
    r"|['\"]\s*(or|and)\s*['\"]?\d)",
    re.IGNORECASE
)

_XSS = re.compile(
    r"(<script|javascript:|on\w+\s*=|<iframe|<object|<embed|data:text/html)",
    re.IGNORECASE
)

_PATH_TRAVERSAL = re.compile(r"\.\./|\.\.\\|%2e%2e[%/\\]", re.IGNORECASE)

_NULL_BYTE = re.compile(r"\x00|%00")

_BAD_AGENTS = re.compile(
    r"(sqlmap|nikto|nmap|masscan|zgrab|python-requests/2\.2[0-9]"
    r"|go-http-client/1\.1|curl/7\.[0-4]\d\.)",
    re.IGNORECASE
)

_MAX_BODY_BYTES = 64 * 1024  # 64 KB


class WAFMiddleware:
    def __init__(self, app, on_block=None):
        self.on_block = on_block
        app.before_request(self._inspect)

    def _inspect(self):
        # 1. Payload size guard
        content_length = request.content_length or 0
        if content_length > _MAX_BODY_BYTES:
            return self._block('payload_too_large')

        # 2. Suspicious user-agent
        ua = request.headers.get('User-Agent', '')
        if _BAD_AGENTS.search(ua):
            return self._block('bad_user_agent')

        # 3. Scan query-string + path
        target = request.full_path + '&'.join(
            f'{k}={v}' for k, v in request.args.items()
        )
        if _NULL_BYTE.search(target):
            return self._block('null_byte')
        if _PATH_TRAVERSAL.search(target):
            return self._block('path_traversal')
        if _SQL_INJECTION.search(target):
            return self._block('sql_injection')
        if _XSS.search(target):
            return self._block('xss')

        # 4. Scan JSON body (read-only peek)
        if request.content_type and 'json' in request.content_type:
            raw = request.get_data(as_text=True)
            if raw:
                if _NULL_BYTE.search(raw):
                    return self._block('null_byte_body')
                if _SQL_INJECTION.search(raw):
                    return self._block('sql_injection_body')
                if _XSS.search(raw):
                    return self._block('xss_body')

    def _block(self, reason: str):
        trace_id = getattr(g, 'trace_id', 'none')
        logger.warning(
            'WAF blocked request',
            extra={
                'trace_id': trace_id,
                'reason': reason,
                'path': request.path,
                'ip': request.remote_addr,
            }
        )
        if self.on_block:
            try:
                self.on_block(reason, request)
            except Exception:
                pass

        return jsonify({
            'error': 'Forbidden',
            'reason': reason,
            'trace_id': trace_id,
        }), 403

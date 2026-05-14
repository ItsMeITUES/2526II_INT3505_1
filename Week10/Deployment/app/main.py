"""
Books API - Production-ready Flask server
Includes: logging, metrics, tracing, rate limiting, circuit breaker, WAF, audit logs
"""

import time
import uuid
import logging
import functools
from datetime import datetime, timezone
from flask import Flask, request, jsonify, g
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.database import db, Book
from app.circuit_breaker import CircuitBreaker
from app.waf import WAFMiddleware
from app.audit import AuditLogger

# ─── Logging Setup ───────────────────────────────────────────────────────────

import logging
from flask import has_request_context

class TraceIdFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            from flask import g
            record.trace_id = getattr(g, 'trace_id', 'none')
        else:
            record.trace_id = 'none'
        return True

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s [%(name)s] [trace_id=%(trace_id)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%SZ'
))
handler.addFilter(TraceIdFilter())

logging.root.setLevel(logging.INFO)
logging.root.handlers = [handler]

logger = logging.getLogger('books_api')

# ─── Prometheus Metrics ───────────────────────────────────────────────────────

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5]
)
ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)
BOOKS_TOTAL = Gauge(
    'books_total',
    'Total books in database'
)
CIRCUIT_BREAKER_STATE = Gauge(
    'circuit_breaker_open',
    'Circuit breaker state (1=open, 0=closed)',
    ['name']
)
RATE_LIMITED_REQUESTS = Counter(
    'rate_limited_requests_total',
    'Total rate-limited requests',
    ['endpoint']
)
WAF_BLOCKED_REQUESTS = Counter(
    'waf_blocked_requests_total',
    'Requests blocked by WAF',
    ['reason']
)

# ─── App Factory ─────────────────────────────────────────────────────────────

def create_app(config=None):
    global app_instance
    app = Flask(__name__)
    app_instance = app

    app.config.update(
        SECRET_KEY='change-me-in-production',
        RATELIMIT_STORAGE_URI='memory://',
        RATELIMIT_HEADERS_ENABLED=True,
    )
    if config:
        app.config.update(config)

    # Init extensions
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_data()

    # Rate limiter — stored on app to prevent GC of the weak reference
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=['100 per minute', '1000 per hour'],
        on_breach=_on_rate_limit_breach
    )
    app.limiter = limiter  # prevent weak-ref GC

    # Circuit breaker for DB operations
    db_breaker = CircuitBreaker(
        name='database',
        failure_threshold=5,
        recovery_timeout=30,
        on_state_change=_on_circuit_state_change
    )

    # WAF
    waf = WAFMiddleware(app, on_block=_on_waf_block)

    # Audit logger
    audit = AuditLogger()

    # ─── Middleware ───────────────────────────────────────────────────────────

    @app.before_request
    def before_request():
        g.start_time = time.monotonic()
        g.trace_id = request.headers.get('X-Trace-Id', str(uuid.uuid4()))
        g.request_id = str(uuid.uuid4())
        ACTIVE_REQUESTS.inc()

        logger.info(
            'Request started',
            extra={
                'trace_id': g.trace_id,
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
        )

    @app.after_request
    def after_request(response):
        latency = time.monotonic() - g.get('start_time', time.monotonic())
        endpoint = request.endpoint or 'unknown'

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(latency)
        ACTIVE_REQUESTS.dec()

        # Inject trace headers
        response.headers['X-Trace-Id'] = g.get('trace_id', 'none')
        response.headers['X-Request-Id'] = g.get('request_id', 'none')
        response.headers['X-Response-Time'] = f'{latency:.4f}s'

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        logger.info(
            'Request completed',
            extra={
                'trace_id': g.get('trace_id', 'none'),
                'status': response.status_code,
                'latency_ms': round(latency * 1000, 2)
            }
        )

        # Audit log for write operations
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            audit.log(
                action=request.method,
                resource=request.path,
                status=response.status_code,
                ip=request.remote_addr,
                trace_id=g.get('trace_id', 'none')
            )

        return response

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found', 'trace_id': g.get('trace_id')}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': str(e.description),
            'trace_id': g.get('trace_id')
        }), 429

    @app.errorhandler(500)
    def server_error(e):
        logger.error('Internal server error', extra={'trace_id': g.get('trace_id', 'none'), 'error': str(e)})
        return jsonify({'error': 'Internal server error', 'trace_id': g.get('trace_id')}), 500

    # ─── Routes ───────────────────────────────────────────────────────────────

    @app.route('/health')
    def health():
        """Liveness probe"""
        return jsonify({'status': 'ok', 'timestamp': _utcnow()})

    @app.route('/ready')
    def ready():
        """Readiness probe — checks DB connectivity"""
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'ready', 'timestamp': _utcnow()})
        except Exception as e:
            logger.error('Readiness check failed', extra={'trace_id': g.get('trace_id', 'none'), 'error': str(e)})
            return jsonify({'status': 'not ready', 'error': 'DB unavailable'}), 503

    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        BOOKS_TOTAL.set(Book.query.count())
        CIRCUIT_BREAKER_STATE.labels(name='database').set(
            1 if db_breaker.is_open else 0
        )
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

    # ─── Books CRUD ───────────────────────────────────────────────────────────

    @app.route('/api/v1/books', methods=['GET'])
    @limiter.limit('60 per minute')
    def list_books():
        """List all books with optional filters"""
        def _query():
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 10, type=int), 100)
            author = request.args.get('author')
            genre = request.args.get('genre')

            q = Book.query
            if author:
                q = q.filter(Book.author.ilike(f'%{author}%'))
            if genre:
                q = q.filter(Book.genre.ilike(f'%{genre}%'))

            paginated = q.order_by(Book.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            return {
                'books': [b.to_dict() for b in paginated.items],
                'total': paginated.total,
                'page': page,
                'per_page': per_page,
                'pages': paginated.pages,
                'trace_id': g.get('trace_id')
            }

        try:
            result = db_breaker.call(_query)
            return jsonify(result)
        except Exception as e:
            logger.error('list_books failed', extra={'trace_id': g.get('trace_id', 'none'), 'error': str(e)})
            return jsonify({'error': 'Service unavailable', 'trace_id': g.get('trace_id')}), 503

    @app.route('/api/v1/books/<int:book_id>', methods=['GET'])
    @limiter.limit('120 per minute')
    def get_book(book_id):
        """Get a single book by ID"""
        # Resolve 404 before hitting the circuit breaker (404 is not a failure)
        book = Book.query.get(book_id)
        if book is None:
            return jsonify({'error': 'Book not found', 'trace_id': g.get('trace_id')}), 404
        return jsonify({'book': book.to_dict(), 'trace_id': g.get('trace_id')})

    @app.route('/api/v1/books', methods=['POST'])
    @limiter.limit('20 per minute')
    def create_book():
        """Create a new book"""
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON body', 'trace_id': g.get('trace_id')}), 400

        errors = _validate_book(data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors, 'trace_id': g.get('trace_id')}), 422

        def _create():
            book = Book(
                title=data['title'].strip(),
                author=data['author'].strip(),
                isbn=data.get('isbn', '').strip() or None,
                genre=data.get('genre', '').strip() or None,
                year=data.get('year'),
                description=data.get('description', '').strip() or None,
            )
            db.session.add(book)
            db.session.commit()
            return book

        try:
            book = db_breaker.call(_create)
            logger.info('Book created', extra={'trace_id': g.get('trace_id', 'none'), 'book_id': book.id})
            return jsonify({'book': book.to_dict(), 'trace_id': g.get('trace_id')}), 201
        except Exception as e:
            db.session.rollback()
            logger.error('create_book failed', extra={'trace_id': g.get('trace_id', 'none'), 'error': str(e)})
            return jsonify({'error': 'Service unavailable', 'trace_id': g.get('trace_id')}), 503

    @app.route('/api/v1/books/<int:book_id>', methods=['PUT'])
    @limiter.limit('20 per minute')
    def update_book(book_id):
        """Full update of a book"""
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON body', 'trace_id': g.get('trace_id')}), 400

        errors = _validate_book(data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors, 'trace_id': g.get('trace_id')}), 422

        def _update():
            book = Book.query.get(book_id)
            if book is None:
                raise KeyError('not found')
            book.title = data['title'].strip()
            book.author = data['author'].strip()
            book.isbn = data.get('isbn', '').strip() or None
            book.genre = data.get('genre', '').strip() or None
            book.year = data.get('year')
            book.description = data.get('description', '').strip() or None
            book.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return book

        try:
            book = db_breaker.call(_update)
            logger.info('Book updated', extra={'trace_id': g.get('trace_id', 'none'), 'book_id': book_id})
            return jsonify({'book': book.to_dict(), 'trace_id': g.get('trace_id')})
        except KeyError:
            return jsonify({'error': 'Book not found', 'trace_id': g.get('trace_id')}), 404
        except Exception as e:
            db.session.rollback()
            logger.error('update_book failed', extra={'trace_id': g.get('trace_id', 'none'), 'error': str(e)})
            return jsonify({'error': 'Service unavailable', 'trace_id': g.get('trace_id')}), 503

    @app.route('/api/v1/books/<int:book_id>', methods=['DELETE'])
    @limiter.limit('10 per minute')
    def delete_book(book_id):
        """Delete a book"""
        def _delete():
            book = Book.query.get(book_id)
            if book is None:
                raise KeyError('not found')
            db.session.delete(book)
            db.session.commit()

        try:
            db_breaker.call(_delete)
            logger.info('Book deleted', extra={'trace_id': g.get('trace_id', 'none'), 'book_id': book_id})
            return jsonify({'message': 'Book deleted', 'trace_id': g.get('trace_id')})
        except KeyError:
            return jsonify({'error': 'Book not found', 'trace_id': g.get('trace_id')}), 404
        except Exception as e:
            db.session.rollback()
            logger.error('delete_book failed', extra={'trace_id': g.get('trace_id', 'none'), 'error': str(e)})
            return jsonify({'error': 'Service unavailable', 'trace_id': g.get('trace_id')}), 503

    return app

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _validate_book(data):
    errors = []
    if not data.get('title') or not str(data['title']).strip():
        errors.append('title is required')
    elif len(data['title']) > 255:
        errors.append('title must be <= 255 characters')
    if not data.get('author') or not str(data['author']).strip():
        errors.append('author is required')
    elif len(data['author']) > 255:
        errors.append('author must be <= 255 characters')
    year = data.get('year')
    if year is not None:
        if not isinstance(year, int) or year < 0 or year > datetime.now().year + 1:
            errors.append('year must be a valid integer')
    isbn = data.get('isbn')
    if isbn and len(str(isbn).replace('-', '').replace(' ', '')) not in (10, 13):
        errors.append('isbn must be 10 or 13 digits')
    return errors

def _utcnow():
    return datetime.now(timezone.utc).isoformat()

def _on_rate_limit_breach(request_limit):
    endpoint = request.endpoint or 'unknown'
    RATE_LIMITED_REQUESTS.labels(endpoint=endpoint).inc()
    logger.warning(
        'Rate limit breached',
        extra={'trace_id': getattr(g, 'trace_id', 'none'), 'endpoint': endpoint, 'limit': str(request_limit)}
    )

def _on_circuit_state_change(name, old_state, new_state):
    logger.warning(f'Circuit breaker [{name}] state: {old_state} → {new_state}')

def _on_waf_block(reason, request):
    WAF_BLOCKED_REQUESTS.labels(reason=reason).inc()
    logger.warning(
        'WAF blocked request',
        extra={'trace_id': getattr(g, 'trace_id', 'none'), 'reason': reason, 'path': request.path}
    )

def _seed_data():
    if Book.query.count() == 0:
        seeds = [
            Book(title='Clean Code', author='Robert C. Martin', genre='Technology', year=2008,
                 isbn='9780132350884', description='A handbook of agile software craftsmanship.'),
            Book(title='The Pragmatic Programmer', author='David Thomas', genre='Technology', year=1999,
                 isbn='9780201616224', description='From journeyman to master.'),
            Book(title='Design Patterns', author='Gang of Four', genre='Technology', year=1994,
                 isbn='9780201633610', description='Elements of reusable object-oriented software.'),
        ]
        for s in seeds:
            db.session.add(s)
        db.session.commit()

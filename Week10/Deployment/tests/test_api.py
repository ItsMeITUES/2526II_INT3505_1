"""
Tests — run with:  pytest tests/ -v
"""

import json
import pytest
from app import create_app
from app.database import db as _db


@pytest.fixture(scope='session')
def app():
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'RATELIMIT_ENABLED': False,
    })
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_books(app):
    """Wipe books table between tests."""
    with app.app_context():
        _db.session.execute(_db.text('DELETE FROM books'))
        _db.session.commit()
    yield


# ── Health / readiness ────────────────────────────────────────────────────────

def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json['status'] == 'ok'


def test_ready(client):
    r = client.get('/ready')
    assert r.status_code == 200
    assert r.json['status'] == 'ready'


def test_metrics(client):
    r = client.get('/metrics')
    assert r.status_code == 200
    assert b'http_requests_total' in r.data


# ── List books ────────────────────────────────────────────────────────────────

def test_list_empty(client):
    r = client.get('/api/v1/books')
    assert r.status_code == 200
    data = r.json
    assert data['books'] == []
    assert data['total'] == 0


def test_list_after_create(client):
    client.post('/api/v1/books',
                json={'title': 'Book A', 'author': 'Alice'},
                content_type='application/json')
    r = client.get('/api/v1/books')
    assert r.status_code == 200
    assert r.json['total'] == 1


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_valid(client):
    payload = {
        'title': 'Clean Code',
        'author': 'Robert C. Martin',
        'genre': 'Technology',
        'year': 2008,
        'isbn': '9780132350884',
    }
    r = client.post('/api/v1/books', json=payload, content_type='application/json')
    assert r.status_code == 201
    book = r.json['book']
    assert book['title'] == 'Clean Code'
    assert book['id'] is not None


def test_create_missing_title(client):
    r = client.post('/api/v1/books', json={'author': 'X'}, content_type='application/json')
    assert r.status_code == 422
    assert 'title is required' in r.json['details']


def test_create_invalid_json(client):
    r = client.post('/api/v1/books', data='not json', content_type='application/json')
    assert r.status_code == 400


def test_create_invalid_year(client):
    r = client.post('/api/v1/books',
                    json={'title': 'X', 'author': 'Y', 'year': 99999},
                    content_type='application/json')
    assert r.status_code == 422


# ── Get ───────────────────────────────────────────────────────────────────────

def test_get_existing(client):
    r = client.post('/api/v1/books',
                    json={'title': 'T', 'author': 'A'},
                    content_type='application/json')
    book_id = r.json['book']['id']
    r2 = client.get(f'/api/v1/books/{book_id}')
    assert r2.status_code == 200
    assert r2.json['book']['id'] == book_id


def test_get_not_found(client):
    r = client.get('/api/v1/books/99999')
    assert r.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

def test_update(client):
    r = client.post('/api/v1/books',
                    json={'title': 'Old', 'author': 'A'},
                    content_type='application/json')
    book_id = r.json['book']['id']
    r2 = client.put(f'/api/v1/books/{book_id}',
                    json={'title': 'New', 'author': 'B'},
                    content_type='application/json')
    assert r2.status_code == 200
    assert r2.json['book']['title'] == 'New'


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete(client):
    r = client.post('/api/v1/books',
                    json={'title': 'T', 'author': 'A'},
                    content_type='application/json')
    book_id = r.json['book']['id']
    r2 = client.delete(f'/api/v1/books/{book_id}')
    assert r2.status_code == 200
    r3 = client.get(f'/api/v1/books/{book_id}')
    assert r3.status_code == 404


# ── Security headers ──────────────────────────────────────────────────────────

def test_security_headers(client):
    r = client.get('/health')
    assert r.headers.get('X-Content-Type-Options') == 'nosniff'
    assert r.headers.get('X-Frame-Options') == 'DENY'
    assert r.headers.get('X-XSS-Protection') == '1; mode=block'


def test_trace_id_propagated(client):
    r = client.get('/health', headers={'X-Trace-Id': 'test-trace-123'})
    assert r.headers.get('X-Trace-Id') == 'test-trace-123'


# ── WAF ───────────────────────────────────────────────────────────────────────

def test_waf_blocks_sql_injection(client):
    r = client.get("/api/v1/books?author=' OR 1=1--")
    assert r.status_code == 403


def test_waf_blocks_xss(client):
    r = client.get('/api/v1/books?title=<script>alert(1)</script>')
    assert r.status_code == 403


def test_waf_blocks_path_traversal(client):
    r = client.get('/api/v1/books?path=../../etc/passwd')
    assert r.status_code == 403


# ── Circuit breaker ───────────────────────────────────────────────────────────

def test_circuit_breaker_opens_on_failures():
    from app.circuit_breaker import CircuitBreaker, CircuitBreakerError

    cb = CircuitBreaker(name='test', failure_threshold=3, recovery_timeout=9999)

    def bad():
        raise RuntimeError('boom')

    for _ in range(3):
        try:
            cb.call(bad)
        except RuntimeError:
            pass

    assert cb.is_open
    with pytest.raises(CircuitBreakerError):
        cb.call(bad)


def test_circuit_breaker_closes_on_success():
    import time
    from app.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(name='test2', failure_threshold=2,
                        recovery_timeout=0, success_threshold=1)

    def bad():
        raise RuntimeError('boom')

    for _ in range(2):
        try:
            cb.call(bad)
        except RuntimeError:
            pass

    assert cb.is_open
    time.sleep(0.05)
    cb.call(lambda: None)  # probe succeeds → CLOSED
    assert not cb.is_open

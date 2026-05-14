"""
Entry point — run with:
  Development:  python wsgi.py
  Production:   gunicorn wsgi:app -w 4 -b 0.0.0.0:8000 --access-logfile -
"""

import os
from app import create_app

app = create_app({
    'SQLALCHEMY_DATABASE_URI': os.getenv(
        'DATABASE_URL', 'sqlite:///books.db'
    ),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SECRET_KEY': os.getenv('SECRET_KEY', 'change-me-in-production'),
    'RATELIMIT_STORAGE_URI': os.getenv('REDIS_URL', 'memory://'),
})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

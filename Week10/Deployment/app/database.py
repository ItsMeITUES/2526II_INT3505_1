"""Database models using Flask-SQLAlchemy (SQLite default, swap for Postgres in production)"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Book(db.Model):
    __tablename__ = 'books'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(255), nullable=False, index=True)
    author      = db.Column(db.String(255), nullable=False, index=True)
    isbn        = db.Column(db.String(20),  nullable=True, unique=True)
    genre       = db.Column(db.String(100), nullable=True, index=True)
    year        = db.Column(db.Integer,     nullable=True)
    description = db.Column(db.Text,        nullable=True)
    created_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':          self.id,
            'title':       self.title,
            'author':      self.author,
            'isbn':        self.isbn,
            'genre':       self.genre,
            'year':        self.year,
            'description': self.description,
            'created_at':  self.created_at.isoformat() if self.created_at else None,
            'updated_at':  self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Book id={self.id} title={self.title!r}>'

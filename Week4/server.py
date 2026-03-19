import os
from flask import Flask, json, jsonify, make_response, request

from flask_cors import CORS

import jwt
import datetime
import bcrypt

from datetime import datetime, timezone, timedelta

from functools import wraps

from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Configurations
PORT = 5000

APIVERSION = 'v3'

BOOKAPI_URL = f'/api/{APIVERSION}/books'

allowCache = True
cacheVisibility = 'public' # public, private, no-cache
cacheDuration = 60 # seconds

API_KEY = os.getenv('API_KEY', 'default_api_key')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'default_db_password')

# Database
booksDatabase = 'data/books.json'
usersDatabase = 'data/users.json'

# Load books from the JSON file
def load_books():

    # Check if the database file exists
    if not os.path.exists(booksDatabase):
        print(f"Error: {booksDatabase} not found.")
        return []
    
    with open(booksDatabase, 'r', encoding='utf-8') as f:
        return json.load(f)
    
# Save books to the JSON file
def save_books(books):
    with open(booksDatabase, 'w', encoding='utf-8') as f:
        json.dump(books, f, indent=4)

# Load users from the JSON file
def load_users():

    # Check if the database file exists
    if not os.path.exists(usersDatabase):
        print(f"Error: {usersDatabase} not found.")
        return []
    
    with open(usersDatabase, 'r', encoding='utf-8') as f:
        return json.load(f)
    
# Save users to the JSON file
def save_users(users):
    with open(usersDatabase, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

#################
# API Endpoints #
#################

# Get all books
@app.route(BOOKAPI_URL, methods=['GET'])
def get_books_with_cache():
    books = load_books(),
    response = make_response(jsonify(books))

    # Add Cache-Control header if caching is allowed
    if allowCache:
        response.headers['Cache-Control'] = f'{cacheVisibility}, max-age={cacheDuration}'
    
    return response, 200

# Add a new book
@app.route(BOOKAPI_URL, methods=['POST'])
def add_book():
    new_book = request.get_json()

    #1. Validate the input
    if not new_book or 'title' not in new_book or 'author' not in new_book:
        if('title' not in new_book):
            return jsonify({"error": "Missing 'title' field"}), 400
        if('author' not in new_book):
            return jsonify({"error": "Missing 'author' field"}), 400

        return jsonify({"error": "Invalid input"}), 400

    #2. Add the new book to the list
    books = load_books()

    # New ID = max existing ID + 1, or 1 if the list is empty
    newId = max([b['id'] for b in books]) + 1 if books else 1
    new_book['id'] = newId
    
    books.append(new_book)

    save_books(books)
    
    #3. Return the newly created book with a 201 status code
    return jsonify(new_book), 201

# Get a book by ID
@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['GET'])
def get_book(book_id):

    books = load_books()

    # Find the book with the given ID
    for b in books:
        if b['id'] == book_id:
            book = b
            return jsonify(book), 200
    
    # If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

# Delete a book by ID
@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):

    books = load_books()

    # Find the book with the given ID and remove it from the list
    for b in books:
        if b['id'] == book_id:
            books.remove(b)
            save_books(books)
            return jsonify({"message": "Book deleted"}), 200
    
    # If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

# Update a book by ID
@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    updated_book = request.get_json()

    #1. Validate the input
    if not updated_book:
        return jsonify({"error": "Invalid input"}), 400
    
    if('title' not in updated_book):
        return jsonify({"error": "Missing 'title' field"}), 400
    if('author' not in updated_book):
        return jsonify({"error": "Missing 'author' field"}), 400
    if('id' not in updated_book):
        return jsonify({"error": "Missing 'id' field"}), 400

    if(updated_book['id'] != book_id):
        return jsonify({"error": "ID in the URL does not match ID in the request body"}), 400

    #2. Find the book with the given ID and update its details
    books = load_books()
    for b in books:
        if b['id'] == book_id:
            b['title'] = updated_book['title']
            b['author'] = updated_book['author']
            save_books(books)
            return jsonify(b), 200
    
    #3. If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

# Partially update a book by ID
@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['PATCH'])
def partially_update_book(book_id):
    updated_fields = request.get_json()

    #1. Validate the input
    if not updated_fields:
        return jsonify({"error": "Invalid input"}), 400
    
    if 'id' in updated_fields and updated_fields['id'] != book_id:
        return jsonify({"error": "ID in the URL does not match ID in the request body"}), 400

    #2. Find the book with the given ID and update its details
    books = load_books()
    for b in books:
        if b['id'] == book_id:
            if 'title' in updated_fields:
                b['title'] = updated_fields['title']
            if 'author' in updated_fields:
                b['author'] = updated_fields['author']
            save_books(books)
            return jsonify(b), 200
    
    #3. If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

# Authentication Endpoints
@app.route('/api/login', methods = ['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    users = load_users()

    for user in users:
        if user['username'] == username:
            user_password_hash = user['password'].encode('utf-8')
            break
    
    if not user_password_hash:
        return jsonify({"error":"Unregistered user."}), 401


    if bcrypt.checkpw(password.encode('utf-8'), user_password_hash):
        now = datetime.now(timezone.utc)
        
        payload = {
            'user_id': username,
            'role': 'admin',
            'exp': now + timedelta(hours=1),
            'iat': now
        }

        token = jwt.encode(payload, API_KEY, algorithm='HS256')

        return jsonify({"accessToken": token})
    
    return jsonify({"error": "Wrong password."}), 401

@app.route('/api/register', methods = ['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    users = load_users()

    if username in users:
        return jsonify({"error":"Username taken."}), 400
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = {
        'username': username,
        'password': hashed_password.decode('utf-8')
    }

    users.append(new_user)
    save_users(users)

    return jsonify({"message": "User registered successfully."}), 201

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1] if " " in auth_header else None

        if not token:
            return jsonify({"error":"No token received."}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
            current_user = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalid."}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/api/protected-data', methods=['GET'])
@token_required
def get_data(current_user):
    return jsonify({"data": "You are accessing protected data!"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=PORT)
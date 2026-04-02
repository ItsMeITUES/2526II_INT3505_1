import os
from flask import Flask, json, jsonify, make_response, request

from flask_cors import CORS

import jwt
import datetime
import bcrypt
from datetime import datetime, timezone, timedelta

from functools import wraps

from dotenv import load_dotenv

from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# Configurations
PORT = 5000

APIVERSION = 'v4'

BOOKAPI_URL = f'/api/{APIVERSION}/books'

AUTHAPI_URL = f'/api/{APIVERSION}/auth'

allowCache = True
cacheVisibility = 'public' # public, private, no-cache
cacheDuration = 60 # seconds

# Environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

tokenExpirationTime =  600 # seconds

# Database
booksDatabase = 'data/books.json'
usersDatabase = 'data/auth.json'

######################
# Database Functions #
######################

# MONGO_URI = os.getenv('MONGO_URI')
# client = MongoClient(MONGO_URI)
# db = client['BookManagementSystem']
# books_collection = db['books']
# users_collection = db['users']

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

############################
# Authentication Endpoints #
############################

@app.route(f'{AUTHAPI_URL}/login', methods = ['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username:
        return jsonify({"error":"Username is required."}), 400
    if not password:
        return jsonify({"error":"Password is required."}), 400

    users = load_users()

    user_password_hash = None

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
            'exp': now + timedelta(seconds=tokenExpirationTime),
            'iat': now
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')  

        return jsonify({"accessToken": token})
    
    return jsonify({"error": "Wrong password."}), 401

@app.route(f'{AUTHAPI_URL}/register', methods = ['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error":"Username and password are required."}), 400

    users = load_users()
    for user in users:
        if user['username'] == username:
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
            data = jwt.decode(token, SECRET_KEY, algorithms='HS256')
            current_user = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalid."}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

######################
# Book API Endpoints #
######################

# Get all books
@app.route(BOOKAPI_URL, methods=['GET'])
def get_books_with_cache():
    books = load_books()

    id = request.args.get('id')
    title = request.args.get('title')
    author = request.args.get('author')

    if id:
        books = [b for b in books if str(b['id']) == id]
    if title:
        books = [b for b in books if b['title'].lower() == title.lower()]
    if author:
        books = [b for b in books if b['author'].lower() == author.lower()]

    try:
        page = int(request.args.get('page', 1))
        pageSize = int(request.args.get('pageSize', 10))
        if page < 1 or pageSize < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters."}), 400

    sumRecords = len(books)
    sumPages = (sumRecords + pageSize - 1) // pageSize

    if page > sumPages and sumPages != 0:
        return jsonify({"error": "Page number out of range."}), 400

    start = (page - 1) * pageSize
    end = start + pageSize

    paginated_books = books[start:end]

    pagination_info = {
        "Total Records": sumRecords,
        "Total Pages": sumPages,
        "currentPage": page,    
        "pageSize": pageSize,
        "hasNextPage": page < sumPages,
        "hasPreviousPage": page > 1
    }

    response = make_response(jsonify({"books": paginated_books, "pagination": pagination_info}))

    # Add Cache-Control header if caching is allowed
    if allowCache:
        response.headers['Cache-Control'] = f'{cacheVisibility}, max-age={cacheDuration}'
    
    return response, 200

# Add a new book
@app.route(BOOKAPI_URL, methods=['POST'])
@token_required
def add_book(current_user):
    new_book = request.get_json()

    #1. Validate the input
    if not new_book or 'title' not in new_book or 'author' not in new_book:
        if('title' not in new_book):
            return jsonify({"error": "Missing 'title' field"}), 400
        if('author' not in new_book):
            return jsonify({"error": "Missing 'author' field"}), 400

        return jsonify({"error": "Invalid input"}), 400

    books = load_books()

    for b in books:
        if b['title'] == new_book['title'] and b['author'] == new_book['author']:
            return jsonify({"error": "Book already exists"}), 400

    #2. Add the new book to the list

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
            response = make_response(jsonify(book))
            if allowCache:  
                response.headers['Cache-Control'] = f'{cacheVisibility}, max-age={cacheDuration}'
            return response, 200
    
    # If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

# Delete a book by ID
@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['DELETE'])
@token_required
def delete_book(current_user, book_id):

    books = load_books()

    # Find the book with the given ID and remove it from the list
    for b in books:
        if b['id'] == book_id:
            books.remove(b)
            save_books(books)
            return jsonify({"message": f"Book with ID {book_id} deleted successfully."}), 200
    
    # If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

# Update a book by ID
@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['PUT'])
@token_required
def update_book(current_user, book_id):
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
@token_required
def partially_update_book(current_user, book_id):
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

@app.route('/api/protected-data', methods=['GET'])
@token_required
def get_data(current_user):
    return jsonify({"data": "You are accessing protected data!"}), 200

if __name__ == '__main__':
    # app.run(debug=True, port=PORT)

    port = int(os.environ.get('PORT', PORT))
    app.run(host='0.0.0.0', port=port)
from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data
books = [
    {"id": 1, "title": "The Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams"},
    {"id": 2, "title": "Project Hail Mary", "author": "Andy Weir"},
    {"id": 3, "title": "The Martian", "author": "Andy Weir"},
    {"id": 4, "title": "Dune", "author": "Frank Herbert"},
]

current_id = 4

# Configurations
PORT = 5000
APIVERSION = 'v1'

BOOKAPI_URL = f'/api/{APIVERSION}/books'

@app.route(BOOKAPI_URL, methods=['GET'])
def get_books():
    return jsonify(books)

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
    current_id += 1
    new_book['id'] = current_id
    books.append(new_book)
    
    #3. Return the newly created book with a 201 status code
    return jsonify(new_book), 201

@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['GET'])
def get_book(book_id):

    # Find the book with the given ID
    for b in books:
        if b['id'] == book_id:
            book = b
            return jsonify(book), 200
    
    # If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

@app.route(f'{BOOKAPI_URL}/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):

    # Find the book with the given ID and remove it from the list
    for b in books:
        if b['id'] == book_id:
            books.remove(b)
            return jsonify({"message": "Book deleted"}), 200
    
    # If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

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
    for b in books:
        if b['id'] == book_id:
            b['title'] = updated_book['title']
            b['author'] = updated_book['author']
            return jsonify(b), 200
    
    #3. If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=PORT)
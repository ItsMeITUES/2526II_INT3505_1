import requests

# Configurations
ServerPort = 5000

APIVERSION = 'v2'

SERVER_URL = f'http://localhost:{ServerPort}/api/{APIVERSION}/books'

def get_all_books():
    response = requests.get(f'{SERVER_URL}')
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None
    
def add_book(title, author):
    new_book = {"title": title, "author": author}
    response = requests.post(f'{SERVER_URL}', json=new_book)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def get_book_by_id(book_id):
    response = requests.get(f'{SERVER_URL}/{book_id}')
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def test_api():
     # Get all books
    print("Test 1. Getting all books...")
    books = get_all_books()
    if books:
        print("Books:", books)
    print("----------------------------------------------")

    # Add a new book
    print("Test 2. Adding a new book...")
    new_book = add_book("The Lord of the Rings", "J.R.R. Tolkien")
    if new_book:
        print("Added Book:", new_book)
    print("----------------------------------------------")

    # Get a book by ID
    print("Test 3. Getting a book by ID...")
    book = get_book_by_id(1)
    if book:
        print("Book by ID:", book)
    print("----------------------------------------------")

    # Get a book by non-existing ID
    print("Test 4. Getting a book by non-existing ID...")
    book = get_book_by_id(-1)
    if not book:
        print("Book with ID -1 not found.")
    print("----------------------------------------------")

    # Update a book
    print("Test 5. Updating a book...")
    updated_book = {"id": 1, "title": "The Hitchhiker's Guide to the Galaxy (Updated)", "author": "Douglas Adams"}
    response = requests.put(f'{SERVER_URL}/1', json=updated_book)
    if response.status_code == 200:
        print("Updated Book:", response.json())
    else:
        print(f"Error: {response.status_code}")
    print("----------------------------------------------")

    # Update a non-existing book
    print("Test 6. Updating a non-existing book...")
    updated_book = {"id": -1, "title": "Non-existing Book", "author": "Unknown"}
    response = requests.put(f'{SERVER_URL}/-1', json=updated_book)
    if response.status_code == 200:
        print("Updated Book:", response.json())
    else:
        print(f"Error: {response.status_code}")
    print("----------------------------------------------")

    # Delete a book
    print("Test 7. Deleting a book...")
    response = requests.delete(f'{SERVER_URL}/5')
    if response.status_code == 200:
        print("Delete Response:", response.json())
    else:
        print(f"Error: {response.status_code}")

    response = requests.get(f'{SERVER_URL}/5')
    if response.status_code == 404:
        print("Book with ID 5 successfully deleted.")
    else:
        print(f"Error: {response.status_code}")

    print("----------------------------------------------")

if __name__ == '__main__':
    test_api()
   

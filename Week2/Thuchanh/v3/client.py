import json
import os

import requests
import time

# Configurations
ServerPort = 5000

SERVER_URL = f'http://localhost:{ServerPort}/api/books'

cachedDataPath = 'cached_books.json'

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
    
def delete_book_by_id(book_id):
    response = requests.delete(f'{SERVER_URL}/{book_id}')
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def update_book(book_id, title, author):
    updated_book = {"id": book_id, "title": title, "author": author}
    response = requests.put(f'{SERVER_URL}/{book_id}', json=updated_book)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def get_all_cached_books():
    if not os.path.exists(cachedDataPath):
        print("No cached data found.")
        return []
    with open(cachedDataPath, 'r') as f:
        return json.load(f)

def get_all_books_with_cache():

    current_time = time.time()

    cachedData = get_all_cached_books()

    timestamp = cachedData.get('timestamp', 0)
    duration = cachedData.get('duration', 0)

    if(not cachedData or current_time - timestamp > duration): # Expired
        print("Cache expired or not found. Fetching from server...")
        response = requests.get(f'{SERVER_URL}')
        if response.status_code == 200:
            books = response.json()
            
            cacheDuration = 0

            if('Cache-Control' in response.headers):
                cache_control = response.headers['Cache-Control']
                print(f"Cache-Control header: {cache_control}")
                if 'max-age' in cache_control:
                    cacheDuration = int(cache_control.split('max-age=')[1].split(',')[0])

            with open(cachedDataPath, 'w') as f:
                json.dump({'timestamp': current_time, 'duration': cacheDuration, 'books': books}, f, indent=4)
            return books
        
        else:
            print(f"Error: {response.status_code}")
            return None
    else:
        print("Using cached data.")
        return cachedData['books']
    
def get_book_by_id_with_cache(book_id):
    books = get_all_books_with_cache()
    for book in books[0]:
        if book['id'] == book_id:
            return book
    print(f"Book with ID {book_id} not found.")
    return None

def clear_cache():
    if not os.path.exists(cachedDataPath):
        print("No cached data found.")
        return
    with open(cachedDataPath, 'w') as f:
        json.dump({}, f)

def test_caching():

    clear_cache()

    print("Testing caching behavior...")
    start_time = time.time()
    books = get_all_books_with_cache()
    end_time = time.time()
    if books:
        print(f"First request took {end_time - start_time:.2f} seconds.")
    
    # Wait for a few seconds and make the same request again
    time.sleep(5)
    
    start_time = time.time()
    books = get_all_books_with_cache()
    end_time = time.time()
    if books:
        print(f"Second request took {end_time - start_time:.2f} seconds.")

    print("----------------------------------------------")

    print("Testing get book by id with cache...")
    start_time = time.time()
    books = get_book_by_id_with_cache(1)
    end_time = time.time()
    if books:
        print(books)
        print(f"First request took {end_time - start_time:.2f} seconds.")

    clear_cache()

    start_time = time.time()
    books = get_book_by_id_with_cache(2)
    end_time = time.time()
    if books:
        print(books)
        print(f"First request took {end_time - start_time:.2f} seconds.")

if __name__ == '__main__':
    # test_api()
    test_caching()
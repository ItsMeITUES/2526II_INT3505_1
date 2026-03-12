from flask import Flask, json, jsonify, make_response, request
import os

app = Flask(__name__)
booksDatabase = 'books.json'

# 
# 1. Tính nhất quán - Consistency
# Các API nên trả về dữ liệu có cấu trúc và định dạng nhất quán để dễ dàng sử dụng và hiểu.
# Ở đây, chúng ta sử dụng JSON để trả về dữ liệu sách, và tất cả các API đều tuân theo cấu trúc này.
#

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    books = [{'id': 1, 'title': 'Book 1', 'author': 'Author 1'}, {'id': 2, 'title': 'Book 2', 'author': 'Author 2'}]
    for b in books:
        if b['id'] == book_id:
            book = b
            return jsonify(book), 200

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

# 
# 2. Tính rõ ràng - Clarity
# Các API nên có tên rõ ràng và dễ hiểu để người dùng biết được chức năng
# Các lỗi nên được xử lý một cách rõ ràng và trả về thông báo lỗi cụ thể để người dùng có thể hiểu và khắc phục.
# 

# Sử dụng đúng HTTP methods (GET, POST, PUT, DELETE) để phản ánh đúng hành động mà API thực hiện. Ví dụ, GET để lấy dữ liệu, POST để tạo mới, PUT để cập nhật và DELETE để xóa.
@app.route('/api/books', methods=['GET'])
@app.route('/api/books', methods=['POST'])
@app.route('/api/books/<int:book_id>', methods=['GET'])
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
@app.route('/api/books/<int:book_id>', methods=['PUT'])

# Các API nên trả về mã trạng thái HTTP phù hợp để phản ánh kết quả của yêu cầu. Ví dụ, 200 OK cho thành công, 201 Created cho khi tạo mới thành công, 400 Bad Request cho lỗi đầu vào và 404 Not Found khi tài nguyên không tồn tại.
@app.route('/api/books', methods=['POST'])
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
    
    #3. Return the newly created book with a 201 status code
    return jsonify(new_book), 201

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    #3. If the book is not found, return a 404 error
    return jsonify({"error": "Book not found"}), 404

# 
# 3. Tính dễ mở rộng - Extensibility
# Các API nên được thiết kế sao cho dễ dàng mở rộng trong tương lai.
# Việc thiết kế phiên bản cho API (ví dụ: /api/v1/books) giúp quản lý các thay đổi và mở rộng trong tương lai mà không làm gián đoạn các phiên bản cũ.
#

# Thay vì dùng
@app.route('/api/books', methods=['GET'])

# Chúng ta có thể sử dụng phiên bản
@app.route('/api/v1/books', methods=['GET'])

# Hoặc đặt riêng biến cho phiên bản
API_VERSION = 'v2'
@app.route(f'/api/{API_VERSION}/books', methods=['GET'])

# Có thể sử dụng Blueprints trong Flask để tổ chức các API theo nhóm.
# Ví dụ, chúng ta có thể tạo một Blueprint cho các API liên quan đến sách và sau đó đăng ký nó với ứng dụng Flask chính.
from flask import Blueprint
books_bp = Blueprint('books', __name__)
@books_bp.route('/books', methods=['GET'])
def get_books():
    books = load_books()
    return jsonify(books) 


#
# CÁC QUY TẮC ĐẶT TÊN    
# Những quy tắc này nhằm đảm bảo rằng các API được đặt tên một cách nhất quán, rõ ràng và dễ hiểu, từ đó cải thiện trải nghiệm của người dùng và khả năng bảo trì của hệ thống. 
#

# 
# 1. Sử dụng plural nouns 
# Tên endpoint phản ánh rằng chúng đại diện cho một tập hợp tài nguyên. Ví dụ: /api/books thay vì /api/book.
# đồng thời không sử dụng động từ trong tên endpoint, vì HTTP methods đã phản ánh hành động mà API thực hiện. Ví dụ: /api/books thay vì /api/get_books.
#

# Nên
@app.route('/api/v1/books', methods=['GET'])

# Không nên
@app.route('/api/v1/get_book', methods=['GET'])

#
# 2. Sử dụng chữ viết thường lowercase
# Tên endpoint nên được viết bằng chữ thường và sử dụng dấu gạch nối để phân tách các từ. Ví dụ: /api/books thay vì /api/Books hoặc /api/books_list.
# Vì giao thức HTTP phân biệt chữ hoa và chữ thường trong đường dẫn URL, việc mặc định sử dụng chữ thường giúp tránh nhầm lẫn và lỗi khi gọi API.
# Một số hệ điều hành có thể xử lý URL một cách khác nhau, VD: myAPI trên Windows có thể được coi là giống myapi, nhưng trên Linux thì không.
# 

# Nên
@app.route('/api/v1/books', methods=['GET'])

# Không nên
@app.route('/api/v1/Books', methods=['GET'])
@app.route('/api/v1/bookList', methods=['GET'])

#
# 3. Sử dụng dấu gạch nối để phân tách các từ
# Khi tên endpoint bao gồm nhiều từ, nên sử dụng dấu gạch nối để phân tách các từ thay vì sử dụng dấu gạch dưới hoặc viết liền. 
# Tránh sử dụng dấu gạch dưới, dấu trắng hoặc CamelCase.
# 

# Nên
@app.route('/api/v1/best-selling-books', methods=['GET'])

# Không nên
@app.route('/api/v1/best_selling_books', methods=['GET'])
@app.route('/api/v1/bestsellingbooks', methods=['GET'])
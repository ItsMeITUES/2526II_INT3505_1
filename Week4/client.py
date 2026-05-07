import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/v3"
AUTH_URL = f"{BASE_URL}/auth"
BOOKS_URL = f"{BASE_URL}/books"

def test_auth_flow():
    # 1. Đăng ký tài khoản mới
    print("--- 1. Đăng ký tài khoản ---")
    reg_data = {"username": "testuser", "password": "mypassword123"}
    r_reg = requests.post(f"{AUTH_URL}/register", json=reg_data)
    print(f"Status: {r_reg.status_code}, Response: {r_reg.json()}")

    # 2. Đăng nhập để lấy Access Token
    print("\n--- 2. Đăng nhập ---")
    login_data = {"username": "testuser", "password": "mypassword123"}
    r_login = requests.post(f"{AUTH_URL}/login", json=login_data)
    
    if r_login.status_code != 200:
        print("Đăng nhập thất bại!")
        return

    token = r_login.json().get("accessToken")
    print(f"Token nhận được: {token[:20]}...")

    # 3. Thử truy cập API yêu cầu Token (Thêm sách)
    print("\n--- 3. Thêm sách (Yêu cầu Token) ---")
    headers = {"Authorization": f"Bearer {token}"}
    book_data = {"title": "Lập trình Python", "author": "Gemini"}
    r_add = requests.post(BOOKS_URL, json=book_data, headers=headers)
    print(f"Status: {r_add.status_code}, Data: {r_add.json()}")

    # 4. Kiểm tra phân quyền Admin (Xóa sách)
    # Lưu ý: Tài khoản 'testuser' mặc định trong code server là role 'user'
    print("\n--- 4. Kiểm tra Admin Role (Xóa sách) ---")
    book_id = r_add.json().get('id') if r_add.status_code == 201 else 1
    r_delete = requests.delete(f"{BOOKS_URL}/{book_id}", headers=headers)
    print(f"Status: {r_delete.status_code} (Mong đợi 403), Response: {r_delete.json()}")

    # 5. Kiểm tra Token hết hạn / sai Token
    print("\n--- 5. Kiểm tra Token sai ---")
    bad_headers = {"Authorization": "Bearer fake_token_here"}
    r_bad = requests.get(f"{BASE_URL}/protected-data", headers=bad_headers)
    print(f"Status: {r_bad.status_code}, Response: {r_bad.json()}")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except requests.exceptions.ConnectionError:
        print("Lỗi: Hãy đảm bảo server.py đang chạy tại http://127.0.0.1:5000")
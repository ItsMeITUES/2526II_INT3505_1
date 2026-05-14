import requests
import time

# Địa chỉ API của bạn (đảm bảo Flask app đang chạy)
URL = "http://127.0.0.1:5000/api/data"

def test_rate_limit():
    print(f"--- Bắt đầu kiểm tra Rate Limit trên: {URL} ---")
    print("Giới hạn thiết lập: 5 lần mỗi phút.\n")

    # Gửi 7 request liên tiếp (vượt quá giới hạn 5)
    for i in range(1, 8):
        try:
            response = requests.get(URL)
            status_code = response.status_code
            
            if status_code == 200:
                print(f"Request {i}: THÀNH CÔNG (200 OK) - Nội dung: {response.text}")
            elif status_code == 429:
                print(f"Request {i}: BỊ CHẶN (429 Too Many Requests) - Bạn đã vượt quá giới hạn!")
            else:
                print(f"Request {i}: LỖI KHÁC ({status_code})")
                
        except requests.exceptions.ConnectionError:
            print("Lỗi: Không thể kết nối tới Server. Hãy đảm bảo app.py đang chạy!")
            break
        
        # Nghỉ một chút giữa các request để quan sát
        time.sleep(0.5)

if __name__ == "__main__":
    test_rate_limit()
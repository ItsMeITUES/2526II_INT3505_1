import os

os.environ['WERKZEUG_COLOR'] = 'false'
os.environ['PY_COLORS'] = '0'

import werkzeug.serving
# Ép werkzeug luôn coi môi trường là không hỗ trợ màu
werkzeug.serving._log_add_style = False

import logging

from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


app = Flask(__name__)



# --- BƯỚC 1: CẤU HÌNH WINSTON-STYLE LOGGING ---
# Thiết lập ghi log ra cả console và file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("app_logs.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- BƯỚC 2: CẤU HÌNH PROMETHEUS METRICS ---
# Khởi tạo metrics và tự động theo dõi các route của Flask
metrics = PrometheusMetrics(app)

# Thêm thông tin tĩnh (tùy chọn)
metrics.info('app_info', 'Flask Application info', version='1.0.0')

# --- BƯỚC 3: CẤU HÌNH RATE LIMITING ---
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


@app.route('/')
def main():
    logger.info("Người dùng truy cập trang chủ")
    return "Hello World!"

@app.route('/api/data')
@limiter.limit("5 per minute")  # Giới hạn 10 request mỗi phút cho route này
def get_data():
    logger.info("API data được gọi")
    return {"status": "success", "data": [1, 2, 3]}

@app.route('/error')
def error():
    logger.error("Đã xảy ra lỗi hệ thống giả lập!")
    return "Internal Server Error", 500

if __name__ == '__main__':
    # Mặc định prometheus-flask-exporter sẽ tạo route /metrics
    app.run(host='0.0.0.0', port=5000)
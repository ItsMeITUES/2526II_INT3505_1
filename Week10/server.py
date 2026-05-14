from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

@app.route("/secure-api")
@limiter.limit("5 per minute") # Tối đa 5 lần mỗi phút
def secure_api():
    return "Đây là API được bảo vệ!"

if __name__ == "__main__":
    app.run(debug=True)
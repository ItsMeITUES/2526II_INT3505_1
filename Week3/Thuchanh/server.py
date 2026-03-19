import jwt
import datetime
import bcrypt

from flask import Flask, request, jsonify

from datetime import datetime, timezone, timedelta

from functools import wraps

app = Flask(__name__)

# Configuration

app.config['SECRET_KEY'] = 'super_secret_key'
PORT = 5000

users_db = {
    "admin": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
    "itues": bcrypt.hashpw("mypassword".encode('utf-8'), bcrypt.gensalt())
}

@app.route('/api/login', methods = ['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user_password_hash = users_db.get(username)
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

        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({"accessToken": token})
    
    return jsonify({"error": "Wrong password."}), 401

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
    

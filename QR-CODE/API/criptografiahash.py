from flask import Flask, request, jsonify, send_file
from hashlib import sha256
from io import BytesIO
import base64
import secrets
import time
import qrcode
import sqlite3


app = Flask(__name__)

tokens_db = {}

expiration_time = 120  # seconds

def hash_token(token):
    return sha256(token.encode()).hexdigest()

@app.route('/api/token', methods=['GET', 'POST'])
def generate_token():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    tokens_db[h] = {
        'expires_at': time.time() + expiration_time,
        'used': False
    }

    return jsonify({
        'token': token,
        'expires_in_seconds': expiration_time,
    })



@app.route('/api/validate', methods=['GET'])
def validate_token():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Token is required.'}), 400

    h = hash_token(token)
    record = tokens_db.get(h)

    if not record:
        return jsonify({'error': 'Invalid token'}), 403

    if time.time() > record['expires_at']:
        return jsonify({'error': 'Token has expired'}), 403

    if record['used']:
        return jsonify({'error': 'Token has already been used'}), 403

    record['used'] = True
    return jsonify({'status': 'Access Granted'})

@app.route('/api/token_qr', methods=['GET', 'POST']) # Apenas para teste, GET pode ser removido depois
def token_qr():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    tokens_db[h] = {
        'expires_at': time.time() + expiration_time,
        'used': False,
    }

    url = f'http://localhost:5000/api/validate?token={token}'

    img = qrcode.make(url)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        'token': token,
        'expires_in_seconds': expiration_time,
        'qr_code_base64': img_str
    })

@app.route('/api/token_qr_json', methods=['GET', 'POST']) # Apenas para teste,GET pode ser removido depois
def token_qr_json():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    tokens_db[h] = {
        'expires_at': time.time() + expiration_time,
        'used': False,
    }

    url = f'http://localhost:5000/api/validate?token={token}'
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    qr_bytes = buf.getvalue()
    qr_b64 = base64.b64encode(qr_bytes).decode()

    return jsonify({
        'token': token,
        'expires_in_seconds': expiration_time,
        'qr_code_base64': qr_b64,
        'verify_url': url
    })
app.run(debug=True)
 


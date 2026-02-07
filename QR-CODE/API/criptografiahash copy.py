from flask import Flask, request, jsonify, send_file
from io import BytesIO
import os
import base64
import secrets
import time
import qrcode
import sqlite3
import hmac

HASH_SECRET = os.environ.get('HASH_SECRET', 'default_secret')  # Substitua por uma chave secreta forte em produção
if not HASH_SECRET:
    raise RuntimeError("HASH_SECRET não definido")
DB_path = 'tokens.db'
MAX_TRIES = 2
MAX_TOKENS_PER_IP = 20
WINDOW_SECONDS = 86400  # 24 horas

def db_delete_expired():
    with sqlite3.connect(DB_path) as conn:
        conn.execute('DELETE FROM tokens WHERE expires_at < ?', (time.time(),))

def init_db():
    with sqlite3.connect(DB_path) as conn:
        # Tabela para armazenar os hashes dos tokens, tempo de expiração, status de uso e número de tentativas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                hash TEXT PRIMARY KEY,
                expires_at REAL,
                used INTEGER,
                tries INTEGER
            )
        ''')
        # Tabela para controle de IPs e tentativas, caso queira implementar bloqueio por IP
        conn.execute('''
        CREATE TABLE IF NOT EXISTS rate_limit (
         ip TEXT PRIMARY KEY,
         count INTEGER,
          reset_at REAL
        )
        ''')

init_db()

app = Flask(__name__)

expiration_time = 120  # seconds

def hash_token(token):
    return hmac.new(
        HASH_SECRET.encode(),
        token.encode(),
        'sha256'
    ).hexdigest()

def db_insert_token(h, expires_at):
    with sqlite3.connect(DB_path) as conn:
        conn.execute('INSERT INTO tokens (hash, expires_at, used, tries) VALUES (?, ?, ?, ?)', (h, expires_at, 0, 0))

def db_get_token(h):
    with sqlite3.connect(DB_path) as conn:
        cur = conn.execute('SELECT expires_at, used, tries FROM tokens WHERE hash = ?', (h,))
        return cur.fetchone()
    
def db_mark_used(h):
    with sqlite3.connect(DB_path) as conn:
        cur = conn.execute(
            'UPDATE tokens SET used = 1 WHERE hash = ?',
            (h,)
        )
        return cur.rowcount > 0  # Retorna True se o token foi marcado como usado

def db_increment_tries(h):
    with sqlite3.connect(DB_path) as conn:
        conn.execute(
            'UPDATE tokens SET tries = tries + 1 WHERE hash = ?',
            (h,)
        )

def db_block_token(h):
    with sqlite3.connect(DB_path) as conn:
        conn.execute(
            'UPDATE tokens SET used = 1 WHERE hash = ?',
            (h,)
        )

def check_rate_limit(ip):
    now = time.time()

    with sqlite3.connect(DB_path) as conn:
        cur = conn.execute(
            'SELECT count, reset_at FROM rate_limit WHERE ip = ?',
            (ip,)
        )
        row = cur.fetchone()

        #IP nunca visto -> cria registro
        if not row:
            conn.execute(
                'INSERT INTO rate_limit (ip, count, reset_at) VALUES (?, ?, ?)',
                (ip, 1, now + WINDOW_SECONDS)
            )
            return True
        
        count, reset_at = row

        #Janela de tempo expirou -> reseta contador
        if now > reset_at:
            conn.execute(
                'UPDATE rate_limit SET count = 1, reset_at = ? WHERE ip = ?',
                (now + WINDOW_SECONDS, ip)
            )
            return True
        
        #Limite de tokens por IP atingido
        if count >= MAX_TOKENS_PER_IP:
            return False
        
        #Incrementa contador
        conn.execute(
            'UPDATE rate_limit SET count = count + 1 WHERE ip = ?',
            (ip,)
        )
        return True

@app.route('/api/token', methods=['GET', 'POST'])
def generate_token():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if not check_rate_limit(ip):
        return jsonify({'error': 'Limite de tokens por IP atingido. Tente novamente em 24h.'}), 429
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    db_delete_expired()
    expires_at = time.time() + expiration_time
    db_insert_token(h, expires_at)
    
    return jsonify({
        'token': token,
        'expires_in_seconds': expiration_time,
    })

@app.route('/api/validate', methods=['GET', 'POST'])
def validate_token():
    data = request.get_json(silent=True) or {}
    token = data.get('token') or request.args.get('token')  # Permite token via query string para GET

    if not token:
        return jsonify({'error': 'Token é obrigatório.'}), 400
    
    db_delete_expired()
    h = hash_token(token)
    row = db_get_token(h)

    if not row:
        # Não damos pistas se o token não existe ou se o hash falhou
        return jsonify({'error': 'Acesso negado'}), 401

    # depois de confirmar que row existe
    expires_at, used, tries = row

    if tries >= MAX_TRIES:
        db_block_token(h)
        return jsonify({'error': 'Token bloqueado por tentativas excessivas'}), 403

    if used:
        db_increment_tries(h)
        return jsonify({'error':'Token inválido ou já utilizado'}), 403
    
    if time.time() > expires_at:
        db_increment_tries(h)
        db_mark_used(h)  # Marca como usado para evitar tentativas futuras
        return jsonify({'error': 'Token expirado'}), 401
    
    updated = db_mark_used(h)

    if not updated:
        return jsonify({'error': 'Token já foi usado'}), 403

    return jsonify({'status': 'Acesso concedido', 'code': 200})

@app.route('/api/token_qr', methods=['POST']) # Apenas para teste, GET pode ser removido depois
def token_qr():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    db_delete_expired()
    expires_at = time.time() + expiration_time
    db_insert_token(h, expires_at)

    base_url = request.host_url.rstrip('/')
    url = f'{base_url}/api/validate?token={token}'

    img = qrcode.make(url)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        'token': token,
        'expires_in_seconds': expiration_time,
        'qr_code_base64': img_str
    })

@app.route('/api/token_qr_json', methods=['POST']) # Apenas para teste,GET pode ser removido depois
def token_qr_json():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    db_delete_expired()
    expires_at = time.time() + expiration_time
    db_insert_token(h, expires_at)


    base_url = request.host_url.rstrip('/') # Remove a barra final para evitar problemas na construção do URL
    url = f'{base_url}/api/validate?token={token}' # Garante que o URL seja construído corretamente, mesmo se a aplicação estiver rodando em um caminho diferente
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

@app.route('/api/token_qr_png', methods=['POST'])
def token_qr_png():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    db_delete_expired()
    expires_at = time.time() + expiration_time
    db_insert_token(h, expires_at)
    

    base_url = request.host_url.rstrip('/')
    url = f'{base_url}/api/validate?token={token}'
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png', as_attachment=True, download_name='token_qr.png')

if __name__ == '__main__':
    app.run()
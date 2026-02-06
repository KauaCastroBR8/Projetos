from flask import Flask, request, jsonify, send_file # flask, request, jsonify servem para criar a API REST, receber os dados e enviar respostas em formato JSON
# send_file é usado para enviar arquivos, como a imagem do QR code, para o cliente
from io import BytesIO # BytesIO é uma classe que permite criar um objeto de arquivo em memória, útil para gerar a imagem do QR code sem precisar salvar no disco
import qrcode # qrcode é uma biblioteca para gerar códigos QR, que serão usados para representar os tokens de acesso
import secrets # secrets é uma biblioteca para gerar tokens seguros, que serão usados para criar os tokens de acesso únicos para cada usuário
import hashlib # hashlib é uma biblioteca para criar hashes, que serão usados para armazenar os tokens de forma segura no banco de dados, evitando que sejam expostos em texto plano
import time # time é uma biblioteca para lidar com o tempo, que será usada para definir a expiração dos tokens e verificar se eles ainda são válidos quando forem usados
from PIL import Image # PIL (Pillow) é uma biblioteca para manipulação de imagens, que será usada para criar a imagem do QR code a partir do token gerado

app = Flask(__name__)

tokens_db = {}

oblivion = 120  # seconds

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

@app.route('/api/token', methods=['GET', 'POST'])
def gerar_token():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    tokens_db[h] = {
        'expira': time.time() + oblivion,
        'usado': False,
        'tentativa': 0
    }

    return jsonify({
        'token': token,
        'expira_em_seg': oblivion
    })

@app.route('/api/validar', methods=['GET'])
def validar():
    token = request.args.get('token')
    if not token:
        return jsonify({'erro': 'Token inexistente.'}), 400

    h = hash_token(token)
    reg = tokens_db.get(h)

    if not reg:
        return jsonify({'erro': 'Token inválido'}), 403

    if time.time() > reg['expira']:
        return jsonify({'erro': 'Token expirado'}), 403

    if reg['usado']:
        return jsonify({'erro': 'Token já utilizado'}), 403

    reg['usado'] = True
    return jsonify({'status': 'Acesso Liberado'})

@app.route('/api/token_qr', methods=['POST'])
def token_qr():
    token = secrets.token_urlsafe(16)
    h = hash_token(token)

    tokens_db[h] = {
        'expira': time.time() + oblivion,
        'usado': False,
        'tentativa': 0
    }

    url = f'http://localhost:5000/api/validar?token={token}'

    img = qrcode.make(url)
    
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')

app.run()
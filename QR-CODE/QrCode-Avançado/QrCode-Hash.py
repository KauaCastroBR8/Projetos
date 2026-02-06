#Qr-Code Com Hashing para Verificação de Integridade

#ideia: Este código gera um QR code + Url com hash "Sha256" para garantir a integridade dos dados.

#Fluxo: QR → /entrada?token=XYZ
       # ↓
#hash(token)
       # ↓
#procura no “banco”
       # ↓
#verifica:
#- existe? Se sim, acesso liberado. Se não, bloqueado.
#- não expirou? Se sim, acesso liberado. Se não, bloqueado.
#- não foi usado? Se sim, acesso liberado. Se não, bloqueado.
#- tentativas ok? Se usado uma vez, acesso liberado. Se não, bloqueado.

from flask import Flask
import secrets
import hashlib

app = Flask(__name__)

#banco de dados simulado para armazenar os hashes dos tokens
tokens_db = {}

@app.route('/verificar')
def gerar():
    token = secrets.token_urlsafe(16)  # Gera um token seguro

    hash_token = hashlib.sha256(token.encode()).hexdigest()  # Calcula o hash do token

    tokens_db[hash_token] ={
        "usado": False
    }
    return f"Token: {token}" # Exibe o token gerado,atualizando a página o codigo é executado novamente e um novo token é gerado

app.run(debug=True)
def verificar(token):
    hash_token = hashlib.sha256(token.encode()).hexdigest()  # Calcula o hash do token


#Primeiro gerar token → combinar hash → guardar hash
#recebe token → calcula hash → compara





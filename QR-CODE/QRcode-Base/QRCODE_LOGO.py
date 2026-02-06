import qrcode
from PIL import Image

dados = input("Digite os dados para gerar o QR Code: ")

# Cria o objeto QR Code

qr = qrcode.QRCode(
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=5,
    border=4,
)

qr.add_data(dados)
qr.make(fit=True)

img = qr.make_image(fill_color="blue", back_color="yellow").convert('RGB')

# Carrega o logo

logo = Image.open("logo.png")

# redimensiona logo

qr_width, qr_height = img.size
tamanho_logo = qr_width // 2
logo = logo.resize((tamanho_logo, tamanho_logo))

# Calcula a posição do logo

posição_logo = ((qr_width - tamanho_logo) // 2, (qr_height - tamanho_logo) // 2)

img.paste(logo, posição_logo, mask=logo)

img.save("qrcode_Logo.PNG")

print("QR Code com logo gerado e salvo como \"qrcode_Logo.PNG\".")
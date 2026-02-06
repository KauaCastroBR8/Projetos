import qrcode
from PIL import Image

#QR-Code rastreavel com logo no centro

#variaveis de entrada
base = input("URL base: ")
fonte = input("Fonte (ex: GitHub): ")
campanha = input("Campanha: ")
url = f"{base}?utm_source={fonte}&utm_campaign={campanha}"

#configurações do QR code
qr = qrcode.QRCode(
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=5,
    border=4,
)
#geração do QR code
qr.add_data(url)
qr.make(fit=True)

#inserção do logo no centro do QR code
img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
logo = Image.open("QRcode-Intermediario/Github-Logo.png").convert("RGBA")

qr_width, qr_height = img.size
tamanho_logo = qr_width // 4
logo = logo.resize((tamanho_logo, tamanho_logo))
posição_logo = ((qr_width - tamanho_logo) // 2, (qr_height - tamanho_logo) // 2)
img.paste(logo, posição_logo, mask=logo.split()[3])

#exibição da URL gerada
print(f"URL gerada: {url}")
img.save("qrcode.png")


import qrcode

dados = input("Digite os dados para gerar o QR Code: ")

qr = qrcode.QRCode(
    version=None,
    box_size=10,
    border=4,
)

qr.add_data(dados)
qr.make(fit=True)

img = qr.make_image(fill_color="blue", back_color="yellow")
img.save("qrcode.png")

print("QR Code gerado e salvo como 'qrcode.png'")
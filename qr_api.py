from flask import Flask, request, send_file
import qrcode
import io
from urllib.parse import quote as url_quote

app = Flask(__name__)

@app.route('/generate_qr', methods=['GET'])
def generate_qr():
    data = request.args.get('data', '')
    if not data:
        return 'No data provided', 400

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return send_file(img_byte_arr, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)

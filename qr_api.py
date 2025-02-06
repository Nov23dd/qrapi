from flask import Flask, request, render_template
import qrcode
import io
import base64
from datetime import datetime
from urllib.parse import quote as url_quote

app = Flask(__name__)
qr_data_list = []

@app.route('/')
def index():
    return render_template('index.html', qr_data=qr_data_list, enumerate=enumerate)

@app.route('/generate', methods=['POST'])
def generate_qr():
    global qr_data_list
    data = request.form['text']
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
    img_str = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
    qr_code = "data:image/png;base64," + img_str

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    qr_data_list.append({'text': data, 'qr_code': qr_code, 'timestamp': timestamp})
    
    return render_template('index.html', qr_data=qr_data_list, enumerate=enumerate)

if __name__ == '__main__':
    app.run(debug=True)

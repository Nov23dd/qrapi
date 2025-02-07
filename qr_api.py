from urllib.parse import quote as url_quote
from flask import Flask, request, render_template, send_file, jsonify
import qrcode
import io
import base64
from datetime import datetime
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

app = Flask(__name__)
qr_data_list = []

@app.route('/')
def index():
    return render_template('index.html', qr_data=qr_data_list, enumerate=enumerate)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    global qr_data_list
    data = request.form['text']
    if not data:
        return jsonify(status='error', message='No data provided')
    
    if any(item['text'] == data for item in qr_data_list):
        return jsonify(status='error', message='Duplicate entry detected')

    qr_code, timestamp = generate_qr_code(data)
    qr_data_list.append({'text': data, 'qr_code': qr_code, 'timestamp': timestamp})
    return jsonify(status='success', qr_data=qr_data_list)

@app.route('/generate_excel')
def generate_excel():
    df = pd.DataFrame(qr_data_list)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='QR Codes')
    writer.save()
    output.seek(0)
    return send_file(output, attachment_filename='qr_codes.xlsx', as_attachment=True)

@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width, height = letter
    
    for idx, item in enumerate(qr_data_list):
        img_data = base64.b64decode(item['qr_code'].split(',')[1])
        img = Image.open(io.BytesIO(img_data))
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        x = 50
        y = height - (idx + 1) * 200  # Adjust the y-position for each QR code
        
        if y < 100:
            c.showPage()
            y = height - 200
        
        c.drawImage(img_io, x, y, width=150, height=150)
        c.drawString(x, y-20, f"Text: {item['text']}")
        c.drawString(x, y-35, f"Timestamp: {item['timestamp']}")

    c.save()
    output.seek(0)
    return send_file(output, attachment_filename='qr_codes.pdf', as_attachment=True)

@app.route('/clear_all', methods=['POST'])
def clear_all():
    global qr_data_list
    qr_data_list = []
    return jsonify(status='success')

def generate_qr_code(data):
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
    return qr_code, timestamp

if __name__ == '__main__':
    app.run(debug=True)

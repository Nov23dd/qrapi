from flask import Flask, request, render_template, jsonify
import qrcode
import io
import base64
from datetime import datetime
import pytz

app = Flask(__name__)
user_data = {
    "Alice": [],
    "Bob": [],
    "Charlie": []
}

@app.route('/')
def cover():
    return render_template('cover.html', users=user_data.keys())

@app.route('/manage_users')
def manage_users():
    return render_template('manage_users.html', users=user_data.keys())

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    if username not in user_data:
        user_data[username] = []
        return jsonify(status='success')
    else:
        return jsonify(status='error', message='User already exists')

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form['username']
    if username in user_data:
        del user_data[username]
        return jsonify(status='success')
    else:
        return jsonify(status='error', message='User not found')

@app.route('/user/<username>')
def user_page(username):
    if username in user_data:
        return render_template('index.html', qr_data=user_data[username], enumerate=enumerate, counter=len(user_data[username]), username=username)
    else:
        return "User not found", 404

@app.route('/generate_qr/<username>', methods=['POST'])
def generate_qr(username):
    if username not in user_data:
        return jsonify(status='error', message='User not found')
    
    data = request.form['text']
    if not data:
        return jsonify(status='error', message='No data provided')
    
    if any(item['text'] == data for item in user_data[username]):
        return jsonify(status='error', message='Duplicate entry detected')

    qr_code, timestamp = generate_qr_code(data)
    user_data[username].append({'text': data, 'qr_code': qr_code, 'timestamp': timestamp})

    return jsonify(status='success', qr_data=user_data[username], counter=len(user_data[username]))

@app.route('/clear_all/<username>', methods=['POST'])
def clear_all(username):
    if username in user_data:
        user_data[username] = []
        return jsonify(status='success')
    else:
        return jsonify(status='error', message='User not found')

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

    tz = pytz.timezone('Asia/Taipei')
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return qr_code, timestamp

if __name__ == '__main__':
    app.run(debug=True)

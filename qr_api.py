from flask import Flask, request, render_template, jsonify
import qrcode
import io
import base64
from datetime import datetime
import pytz
from weasyprint import HTML

app = Flask(__name__)

# 將 enumerate 函數添加到模板環境中
app.jinja_env.globals.update(enumerate=enumerate)

# 初始化用戶數據
user_data = {
    "Alice": [],
    "Bob": [],
    "Charlie": []
}

@app.route('/')
def cover():
    """渲染封面頁面"""
    return render_template('cover.html', users=user_data.keys())

@app.route('/manage_users')
def manage_users():
    """渲染用戶管理頁面"""
    return render_template('manage_users.html', users=user_data.keys())

@app.route('/add_user', methods=['POST'])
def add_user():
    """添加用戶"""
    username = request.form['username']
    if username not in user_data:
        user_data[username] = []
        return jsonify(status='success')
    else:
        return jsonify(status='error', message='User already exists')

@app.route('/delete_user', methods=['POST'])
def delete_user():
    """刪除用戶"""
    username = request.form['username']
    if username in user_data:
        del user_data[username]
        return jsonify(status='success')
    else:
        return jsonify(status='error', message='User not found')

@app.route('/user/<username>')
def user_page(username):
    """渲染用戶頁面"""
    if username in user_data:
        return render_template('index.html', qr_data=user_data[username], counter=len(user_data[username]), username=username)
    else:
        return "User not found", 404

@app.route('/generate_qr/<username>', methods=['POST'])
def generate_qr(username):
    """生成 QR Code"""
    if username not in user_data:
        return jsonify(status='error', message='User not found')
    
    data = request.form['text']
    if not data:
        return jsonify(status='error', message='No data provided')
    
    if any(item['text'] == data for item in user_data[username]):
        return jsonify(status='error', message='Duplicate entry detected')

    qr_code, timestamp = generate_qr_code(data)
    user_data[username].append({'text': data, 'qr_code': qr_code, 'timestamp': timestamp})

    # 重新按時間順序排列 qr_data
    user_data[username] = sorted(user_data[username], key=lambda x: x['timestamp'])

    # 計算總共處理件數
    total_items = len(user_data[username])

    return jsonify(status='success', qr_data=user_data[username], counter=total_items)

@app.route('/clear_all/<username>', methods=['POST'])
def clear_all(username):
    """清除所有 QR Code"""
    if username in user_data:
        user_data[username] = []
        return jsonify(status='success', counter=0)
    else:
        return jsonify(status='error', message='User not found')

@app.route('/export_pdf/<username>', methods=['POST'])
def export_pdf(username):
    """匯出 PDF"""
    if username not in user_data:
        return jsonify(status='error', message='User not found')

    # 將刷貨頁面內容轉換為 HTML
    html_content = render_template('pdf_template.html', qr_data=user_data[username], username=username)

    # 使用 WeasyPrint 將 HTML 轉換為 PDF
    pdf = HTML(string=html_content).write_pdf()

    # 生成日期和用戶名的檔案名稱
    tz = pytz.timezone('Asia/Taipei')
    current_date = datetime.now(tz).strftime("%y%m%d")  # 生成格式 250208
    total_items = len(user_data[username])
    file_name = f"{current_date}蝦皮預刷ll{total_items}.pdf"

    # 將 PDF 編碼為 base64
    pdf_base64 = base64.b64encode(pdf).decode('utf-8')

    return jsonify(status='success', pdf=pdf_base64, file_name=file_name)

def generate_qr_code(data):
    """生成 QR Code 圖片和時間戳"""
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

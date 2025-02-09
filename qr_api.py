from flask import Flask, request, render_template, jsonify, g
import qrcode
import io
import base64
from datetime import datetime
import pytz
from weasyprint import HTML
import sqlite3

app = Flask(__name__)
DATABASE = 'user_data.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def add_user_to_db(username):
    db = get_db()
    db.execute('INSERT INTO users (username) VALUES (?)', (username,))
    db.commit()

def delete_user_from_db(username):
    db = get_db()
    db.execute('DELETE FROM users WHERE username = ?', (username,))
    db.commit()
@app.route('/')
def cover():
    users = [row[0] for row in query_db('SELECT username FROM users')]
    return render_template('cover.html', users=users)

@app.route('/manage_users')
def manage_users():
    users = [row[0] for row in query_db('SELECT username FROM users')]
    return render_template('manage_users.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    if not username or len(username) < 3:
        return jsonify(status='error', message='Invalid username. Username must be at least 3 characters long.')
    if query_db('SELECT * FROM users WHERE username = ?', (username,), one=True):
        return jsonify(status='error', message='User already exists')
    add_user_to_db(username)
    users = [row[0] for row in query_db('SELECT username FROM users')]
    return jsonify(status='success', users=users)

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form['username']
    if not username:
        return jsonify(status='error', message='No username provided')
    if not query_db('SELECT * FROM users WHERE username = ?', (username,), one=True):
        return jsonify(status='error', message='User not found')
    delete_user_from_db(username)
    users = [row[0] for row in query_db('SELECT username FROM users')]
    return jsonify(status='success', users=users)

@app.route('/user/<username>')
def user_page(username):
    if not query_db('SELECT * FROM users WHERE username = ?', (username,), one=True):
        return "User not found", 404
    qr_data = query_db('SELECT text, qr_code, timestamp FROM qr_codes WHERE username = ?', (username,))
    return render_template('index.html', qr_data=qr_data, counter=len(qr_data), username=username)

@app.route('/generate_qr/<username>', methods=['POST'])
def generate_qr(username):
    if not query_db('SELECT * FROM users WHERE username = ?', (username,), one=True):
        return jsonify(status='error', message='User not found')

    data = request.form['text']
    if not data or len(data) < 15:
        return jsonify(status='error', message='Invalid data provided')

    if query_db('SELECT * FROM qr_codes WHERE username = ? AND text = ?', (username, data), one=True):
        return jsonify(status='error', message='Duplicate entry detected')

    try:
        qr_code, timestamp = generate_qr_code(data)
        db = get_db()
        db.execute('INSERT INTO qr_codes (username, text, qr_code, timestamp) VALUES (?, ?, ?, ?)', (username, data, qr_code, timestamp))
        db.commit()

        qr_data = query_db('SELECT text, qr_code, timestamp FROM qr_codes WHERE username = ?', (username,))
        total_items = len(qr_data)

        return jsonify(status='success', qr_data=qr_data, counter=total_items)
    except Exception as e:
        return jsonify(status='error', message=str(e))

@app.route('/clear_all/<username>', methods=['POST'])
def clear_all(username):
    if not query_db('SELECT * FROM users WHERE username = ?', (username,), one=True):
        return jsonify(status='error', message='User not found')

    db = get_db()
    db.execute('DELETE FROM qr_codes WHERE username = ?', (username,))
    db.commit()

    return jsonify(status='success', counter=0)

@app.route('/export_pdf/<username>', methods=['POST'])
def export_pdf(username):
    if not query_db('SELECT * FROM users WHERE username = ?', (username,), one=True):
        return jsonify(status='error', message='User not found')

    try:
        qr_data = query_db('SELECT text, qr_code, timestamp FROM qr_codes WHERE username = ?', (username,))
        html_content = render_template('pdf_template.html', qr_data=qr_data, username=username)

        pdf = HTML(string=html_content).write_pdf()

        tz = pytz.timezone('Asia/Taipei')
        current_date = datetime.now(tz).strftime("%y%m%d")
        total_items = len(qr_data)
        file_name = f"{current_date}蝦皮預刷ll{total_items}.pdf"

        pdf_base64 = base64.b64encode(pdf).decode('utf-8')

        return jsonify(status='success', pdf=pdf_base64, file_name=file_name)
    except Exception as e:
        return jsonify(status='error', message=str(e))

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
    init_db()
    app.run(debug=True)

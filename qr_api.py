from flask import Flask, request, render_template, jsonify, g, current_app, send_file
import qrcode
import io
import base64
from datetime import datetime, timedelta
import pytz
from weasyprint import HTML
import sqlite3
import os
import logging
from logging.handlers import RotatingFileHandler
import psutil  # Importing psutil for memory usage logging

class Config:
    DATABASE = os.getenv('DATABASE', 'user_data.db')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    TIMEZONE = 'Asia/Taipei'

def setup_logging(app):
    if not os.path.exists('logs'):
        os.makedirs('logs')
    handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def query_db(query, args=(), one=False):
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        get_db().commit()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        current_app.logger.error(f"Database error: {e}")
        raise

def init_db(app):
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def validate_username(username):
    if not username or not isinstance(username, str):
        return False
    if len(username) < 3 or len(username) > 50:
        return False
    if not username.isalnum():
        return False
    return True

def generate_qr_code(data):
    if len(data) > 2048:
        raise ValueError("Data too long for QR code")
    
    tz = pytz.timezone(current_app.config['TIMEZONE'])
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
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
        return f"data:image/png;base64,{img_str}", timestamp
    except Exception as e:
        current_app.logger.error(f"Error generating QR code: {e}")
        raise

def delete_user_from_db(username):
    db = get_db()
    db.execute('DELETE FROM users WHERE username = ?', [username])
    db.commit()

def row_to_dict(row):
    return {key: row[key] for key in row.keys()}

def paginate_data(data, page_size):
    """Split data into chunks of a specified page size."""
    for i in range(0, len(data), page_size):
        yield data[i:i + page_size]

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    setup_logging(app)
    
    # Register teardown context
    @app.teardown_appcontext
    def close_connection(exception):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # Register template filters
    @app.template_filter('enumerate')
    def enumerate_filter(iterable, start=0):
        return enumerate(iterable, start=start)
    
    # Initialize database if it doesn't exist
    if not os.path.exists(app.config['DATABASE']):
        with app.app_context():
            init_db(app)
    
    @app.route('/')
    def cover():
        try:
            users = query_db('SELECT username FROM users')
            return render_template('cover.html', users=[row['username'] for row in users])
        except Exception as e:
            app.logger.error(f"Error in cover route: {e}")
            return str(e), 500

    @app.route('/manage_users')
    def manage_users():
        try:
            users = query_db('SELECT username FROM users')
            users_with_index = list(enumerate([row['username'] for row in users], start=1))
            return render_template('manage_users.html', users=users_with_index)
        except Exception as e:
            app.logger.error(f"Error in manage_users route: {e}")
            return str(e), 500

    @app.route('/add_user', methods=['POST'])
    def add_user():
        username = request.form['username']
        if not username or len(username) < 3:
            return jsonify(status='error', message='Invalid username. Username must be at least 3 characters long.')
        if query_db('SELECT * FROM users WHERE username = ?', [username], one=True):
            return jsonify(status='error', message='User already exists')
        
        try:
            db = get_db()
            db.execute('INSERT INTO users (username) VALUES (?)', [username])
            db.commit()
            users = [row['username'] for row in query_db('SELECT username FROM users')]
            return jsonify(status='success', users=users)
        except Exception as e:
            app.logger.error(f"Error adding user: {e}")
            return jsonify(status='error', message='Database error'), 500

    @app.route('/delete_user', methods=['POST'])
    def delete_user():
        username = request.form['username']
        if not validate_username(username):
            current_app.logger.warning(f"Invalid username: {username}")
            return jsonify(status='error', message='Invalid username.')
        if not query_db('SELECT * FROM users WHERE username = ?', [username], one=True):
            current_app.logger.warning(f"User not found: {username}")
            return jsonify(status='error', message='User not found')
    
        try:
            delete_user_from_db(username)
            users = [row['username'] for row in query_db('SELECT username FROM users')]
            return jsonify(status='success', users=users)
        except Exception as e:
            current_app.logger.error(f"Error deleting user: {e}")
            return jsonify(status='error', message='Database error'), 500

    @app.route('/user/<username>')
    def user_page(username):
        if not validate_username(username):
            return jsonify(error="Invalid username"), 400
        try:
            user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
            if user is None:
                return jsonify(error="User not found"), 404
            
            qr_data = query_db(
                'SELECT text, qr_code, timestamp FROM qr_codes WHERE username = ?', 
                [username]
            )
            qr_data = [row_to_dict(row) for row in qr_data]
            return render_template('index.html', 
                                 qr_data=qr_data, 
                                 counter=len(qr_data), 
                                 username=username)
        except Exception as e:
            app.logger.error(f"Error in user_page: {e}")
            return jsonify(error="Internal server error"), 500

    @app.route('/generate_qr/<username>', methods=['POST'])
    def generate_qr_endpoint(username):
        if not query_db('SELECT * FROM users WHERE username = ?', [username], one=True):
            return jsonify(status='error', message='User not found')

        data = request.form['text']
        if not data or len(data) < 15:
            return jsonify(status='error', message='Invalid data provided')
        
        try:
            qr_code, timestamp = generate_qr_code(data)
            db = get_db()
            db.execute('INSERT INTO qr_codes (username, text, qr_code, timestamp) VALUES (?, ?, ?, ?)',
                      [username, data, qr_code, timestamp])
            db.execute('INSERT INTO user_data (username, timestamp, qr_data) VALUES (?, ?, ?)',
                      [username, timestamp, data])
            db.commit()

            qr_data = query_db('SELECT text, qr_code, timestamp FROM qr_codes WHERE username = ?',
                             [username])
            qr_data = [row_to_dict(row) for row in qr_data]
            
            # Clean up old records
            one_week_ago = datetime.now() - timedelta(days=7)
            db.execute('DELETE FROM user_data WHERE timestamp < ?',
                      [one_week_ago.strftime("%Y-%m-%d %H:%M:%S")])
            db.commit()
            
            return jsonify(status='success', qr_data=qr_data, counter=len(qr_data))
        except Exception as e:
            app.logger.error(f"Error generating QR code: {e}")
            return jsonify(status='error', message=str(e))

    @app.route('/clear_all/<username>', methods=['POST'])
    def clear_all(username):
        if not query_db('SELECT * FROM users WHERE username = ?', [username], one=True):
            return jsonify(status='error', message='User not found')

        try:
            db = get_db()
            db.execute('DELETE FROM qr_codes WHERE username = ?', [username])
            db.commit()
            return jsonify(status='success', counter=0)
        except Exception as e:
            app.logger.error(f"Error clearing data: {e}")
            return jsonify(status='error', message='Database error'), 500

    @app.route('/scan_records/<username>', methods=['GET'])
    def scan_records(username):
        if not validate_username(username):
            return jsonify(status='error', message='Invalid username')
            
        try:
            if not query_db('SELECT * FROM users WHERE username = ?', [username], one=True):
                return jsonify(status='error', message='User not found')

            date = request.args.get('date')
            if date:
                records = query_db(
                    'SELECT * FROM user_data WHERE username = ? AND DATE(timestamp) = DATE(?)',
                    [username, date]
                )
            else:
                records = query_db(
                    'SELECT * FROM user_data WHERE username = ?',
                    [username]
                )
            records = [row_to_dict(row) for row in records]
            
            # Get unique dates
            dates = query_db(
                'SELECT DISTINCT DATE(timestamp) as date FROM user_data WHERE username = ? ORDER BY date DESC',
                [username]
            )
            dates = [row['date'] for row in dates]
            
            return jsonify(status='success', records=records, dates=dates)
        except Exception as e:
            app.logger.error(f"Error fetching scan records: {e}")
            return jsonify(status='error', message='Internal server error')

    @app.route('/delete_record/<username>', methods=['POST'])
    def delete_record(username):
        if not validate_username(username):
            return jsonify(status='error', message='Invalid username')

        record_id = request.form.get('id')
        if not record_id:
            return jsonify(status='error', message='Record ID not provided')

        try:
            db = get_db()
            db.execute('DELETE FROM user_data WHERE id = ? AND username = ?', [record_id, username])
            db.commit()
            return jsonify(status='success')
        except Exception as e:
            app.logger.error(f"Error deleting record: {e}")
            return jsonify(status='error', message='Database error')

    @app.route('/scan_complete/<username>', methods=['POST'])
    def scan_complete(username):
        if not query_db('SELECT * FROM users WHERE username = ?', [username], one=True):
            return jsonify(status='error', message='User not found')

        try:
            qr_data = query_db('SELECT text, qr_code, timestamp FROM qr_codes WHERE username = ?', [username])
            qr_data = [row_to_dict(row) for row in qr_data]
            tz = pytz.timezone(app.config['TIMEZONE'])
            for item in qr_data:
                db = get_db()
                db.execute('INSERT INTO user_data (username, timestamp, qr_data) VALUES (?, ?, ?)',
                           [username, item['timestamp'], item['text']])
                db.commit()
        except Exception as e:
            app.logger.error(f"Error storing scan records: {e}")
            return jsonify(status='error', message=f"Error storing scan records: {e}")

        # Export PDF with pagination
        try:
            page_size = 50  # Adjust page size as needed
            paginated_data = list(paginate_data(qr_data, page_size))
            pdfs = []

            for index, page_data in enumerate(paginated_data):
                html_content = render_template('pdf_template.html', qr_data=page_data, username=username)
                app.logger.info(f"Memory usage before PDF generation (Page {index + 1}): {psutil.virtual_memory().percent}%")
                pdf = HTML(string=html_content).write_pdf()
                app.logger.info(f"Memory usage after PDF generation (Page {index + 1}): {psutil.virtual_memory().percent}%")
                pdfs.append(pdf)

            # Combine PDF pages if needed
            combined_pdf = b''.join(pdfs)
            current_date = datetime.now(tz).strftime("%y%m%d")
            total_items = len(qr_data)
            file_name = f"{current_date}蝦皮預刷ll{total_items}.pdf"
            pdf_base64 = base64.b64encode(combined_pdf).decode('utf-8')
            return jsonify(status='success', pdf=pdf_base64, file_name=file_name)
        except Exception as e:
            app.logger.error(f"Error exporting PDF: {e}")
            return jsonify(status='error', message=f"Error exporting PDF: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
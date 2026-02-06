import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename # ตัวช่วยตั้งชื่อไฟล์ให้ปลอดภัย

app = Flask(__name__)

# กำหนดโฟลเดอร์สำหรับเก็บไฟล์อัปโหลด
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# สร้างโฟลเดอร์รอไว้เลย (ถ้ายังไม่มี)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ฟังก์ชันเช็คสกุลไฟล์
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# จำลอง Database
posts_db = [
    {
        'id': 1,
        'title': 'ยินดีต้อนรับสู่ Webboard!',
        'author': 'Admin',
        'content': 'ระบบรองรับการอัปโหลดไฟล์แล้วนะ',
        'media': '', # ไม่มีรูป
        'media_type': 'none',
        'timestamp': '2025-01-01 12:00'
    }
]

@app.route('/')
def home():
    query = request.args.get('q')
    if query:
        filtered_posts = [p for p in posts_db if query.lower() in p['title'].lower() or query.lower() in p['content'].lower()]
        posts_to_show = filtered_posts
    else:
        posts_to_show = posts_db
    return render_template('index.html', posts=reversed(posts_to_show))

@app.route('/friends')
def friends_page():
    return render_template('index.html', posts=[])

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        
        # --- ส่วนจัดการไฟล์อัปโหลด ---
        media_filename = None
        media_type = 'none'

        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # บันทึกไฟล์ลงเครื่อง
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                # เก็บ Path ของไฟล์ไว้ใน DB
                media_filename = f'uploads/{filename}'
                
                # เช็คว่าเป็นวิดีโอหรือไม่
                if filename.lower().endswith(('.mp4', '.mov', '.avi')):
                    media_type = 'video'
                else:
                    media_type = 'image'

        # คำนวณเวลาไทย
        thai_time = datetime.utcnow() + timedelta(hours=7)
        formatted_time = thai_time.strftime("%d/%m/%Y %H:%M")

        new_post = {
            'id': len(posts_db) + 1,
            'title': title,
            'author': author,
            'content': content,
            'media': media_filename,     # เก็บชื่อไฟล์
            'media_type': media_type,    # เก็บประเภท (รูป/วิดีโอ)
            'timestamp': formatted_time
        }
        posts_db.append(new_post)
        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/status')
def status_check():
    CLOUD_FUNCTION_URL = "https://check-status-final-88358153370.asia-southeast1.run.app"
    return redirect(CLOUD_FUNCTION_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
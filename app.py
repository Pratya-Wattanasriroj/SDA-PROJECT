import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- ตั้งค่าโฟลเดอร์สำหรับเก็บไฟล์ ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # สร้างโฟลเดอร์อัตโนมัติถ้ายังไม่มี

# ฟังก์ชันตรวจสอบนามสกุลไฟล์
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- จำลอง Database (ปรับให้รองรับ media_list) ---
posts_db = [
    {
        'id': 1,
        'title': 'ยินดีต้อนรับสู่ Webboard555!',
        'author': 'Admin',
        'content': 'ตอนนี้ระบบรองรับการอัปโหลดหลายรูปแล้วนะ ลองกดดูสิ!',
        'media_list': [], # เป็นลิสต์ว่างไว้ก่อน
        'timestamp': '01/01/2026 12:00'
    }
]

@app.route('/')
def home():
    query = request.args.get('q')
    if query:
        # ระบบค้นหา
        filtered_posts = [p for p in posts_db if query.lower() in p['title'].lower() or query.lower() in p['content'].lower()]
        posts_to_show = filtered_posts
    else:
        posts_to_show = posts_db
    
    # ส่งข้อมูลไปหน้าเว็บ (เรียงจากใหม่ไปเก่า)
    return render_template('index.html', posts=reversed(posts_to_show))

@app.route('/friends')
def friends_page():
    # หน้าเพื่อน (ยังไม่มีข้อมูล)
    return render_template('index.html', posts=[])

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        
        # --- ส่วนจัดการไฟล์ (รองรับหลายไฟล์) ---
        media_list = []
        
        # ตรวจสอบว่ามีการส่งไฟล์มาหรือไม่
        if 'file' in request.files:
            files = request.files.getlist('file') # รับไฟล์ทั้งหมดเป็น List
            
            for file in files:
                # เช็คว่าไฟล์มีชื่อและนามสกุลถูกต้อง
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # บันทึกไฟล์
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    
                    # เช็คว่าเป็นวิดีโอหรือไม่
                    m_type = 'image'
                    if filename.lower().endswith(('.mp4', '.mov', '.avi')):
                        m_type = 'video'
                    
                    # เพิ่มข้อมูลไฟล์ลงใน List
                    media_list.append({
                        'filename': f'uploads/{filename}',
                        'type': m_type
                    })

        # --- จัดการเวลา (Timezone ไทย) ---
        thai_time = datetime.utcnow() + timedelta(hours=7)
        formatted_time = thai_time.strftime("%d/%m/%Y %H:%M")

        # สร้างโพสต์ใหม่
        new_post = {
            'id': len(posts_db) + 1,
            'title': title,
            'author': author,
            'content': content,
            'media_list': media_list, # เก็บเป็น List
            'timestamp': formatted_time
        }
        
        posts_db.append(new_post)
        return redirect(url_for('home'))
        
    return render_template('create.html')

@app.route('/status')
def status_check():
    # ลิงก์ Cloud Function ของคุณ
    CLOUD_FUNCTION_URL = "https://check-status-final-88358153370.asia-southeast1.run.app"
    return redirect(CLOUD_FUNCTION_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
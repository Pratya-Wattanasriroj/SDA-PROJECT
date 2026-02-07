import os
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash # สำหรับเข้ารหัสรหัสผ่าน
from flask_sqlalchemy import SQLAlchemy # ฐานข้อมูล
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user # ระบบล็อกอิน

app = Flask(__name__)

# --- ตั้งค่า Config ---
app.secret_key = 'super_secret_key_change_this' # จำเป็นมากสำหรับ Login Session
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # สร้างไฟล์ DB ชื่อ database.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# สร้างตัวจัดการ
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # ถ้ายังไม่ล็อกอิน ให้ดีดไปหน้า login

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

# --- สร้างตาราง Database (Model) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) # เก็บแบบ Hash

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False) # เก็บชื่อคนโพสต์
    media_list = db.Column(db.Text, nullable=True) # เก็บ Path ไฟล์ (แปลงเป็น String)
    timestamp = db.Column(db.String(50), nullable=False)

# สร้าง Database จริงๆ
with app.app_context():
    db.create_all()

# ฟังก์ชันโหลด User (Flask-Login ต้องการ)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ฟังก์ชันตรวจสอบไฟล์
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---

@app.route('/')
def home():
    # ดึงข้อมูลจาก Database
    posts = Post.query.order_by(Post.id.desc()).all()
    
    # วนลูปกระทู้เพื่อเตรียมไฟล์ (Pre-process)
    for post in posts:
        post.struct_media = [] # สร้างตัวแปรใหม่สำหรับเก็บข้อมูลไฟล์ที่จัดระเบียบแล้ว
        
        if post.media_list:
            # แยกไฟล์ด้วยลูกน้ำ
            file_paths = post.media_list.split(',')
            
            for path in file_paths:
                path = path.strip() # ลบช่องว่างหน้าหลังออก (กันเหนียว)
                if not path: continue # ถ้าเป็นค่าว่างให้ข้ามไป
                
                # เช็คประเภทไฟล์ตรงนี้เลย (Python แม่นยำที่สุด)
                m_type = 'image'
                if path.lower().endswith(('.mp4', '.mov', '.avi')):
                    m_type = 'video'
                
                # เก็บข้อมูลแบบมีโครงสร้าง
                post.struct_media.append({
                    'path': path,
                    'type': m_type
                })
        else:
            post.struct_media = []
            
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # เช็คว่าชื่อซ้ำไหม
        if User.query.filter_by(username=username).first():
            flash('ชื่อนี้มีคนใช้แล้วครับ เปลี่ยนใหม่นะ')
            return redirect(url_for('register'))
        
        # เข้ารหัสรหัสผ่าน (เพื่อความปลอดภัย)
        hashed_pw = generate_password_hash(password, method='scrypt')
        
        # บันทึกลง DB
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash('สมัครสมาชิกสำเร็จ! ล็อกอินได้เลย')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        # เช็คว่ามี user นี้ และรหัสผ่านถูกต้อง
        if user and check_password_hash(user.password, password):
            login_user(user) # สั่งล็อกอิน
            return redirect(url_for('home'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
            
    return render_template('login.html')

@app.route('/logout')
@login_required # ต้องล็อกอินก่อนถึงจะกดได้
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create', methods=['GET', 'POST'])
@login_required # บังคับล็อกอินถึงจะโพสต์ได้!
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # ไม่ต้องรับชื่อจากฟอร์มแล้ว ใช้ชื่อคนล็อกอินเลย
        author = current_user.username 
        
        media_paths = []
        if 'file' in request.files:
            files = request.files.getlist('file')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    media_paths.append(f'uploads/{filename}')
        
        # รวม Path ไฟล์เป็น String คั่นด้วยจุลภาค (ง่ายต่อการเก็บใน SQLite)
        media_string = ",".join(media_paths)

        thai_time = datetime.utcnow() + timedelta(hours=7)
        formatted_time = thai_time.strftime("%d/%m/%Y %H:%M")

        # บันทึกลง DB
        new_post = Post(title=title, content=content, author=author, media_list=media_string, timestamp=formatted_time)
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/status')
def status_check():
    return redirect("https://check-status-final-88358153370.asia-southeast1.run.app") # ใส่ Link เดิมของคุณ

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
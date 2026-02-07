import os
import uuid # เพิ่มตัวช่วยตั้งชื่อไฟล์สุ่ม
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# Config
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# นามสกุลที่อนุญาต
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm', 'mkv'}

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    media_list = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.String(50), nullable=False)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---

@app.route('/')
def home():
    posts = Post.query.order_by(Post.id.desc()).all()
    
    # กำหนดนามสกุลวิดีโอ
    VIDEO_EXTS = {'mp4', 'mov', 'avi', 'webm', 'mkv'}

    for post in posts:
        post.struct_media = []
        if post.media_list:
            paths = post.media_list.split(',')
            for p in paths:
                p = p.strip()
                if not p: continue
                
                # Logic เช็คไฟล์
                # ดึงนามสกุลจาก path (เช่น uploads/xxxx.mp4 -> mp4)
                try:
                    ext = p.split('.')[-1].lower()
                except:
                    ext = ""
                
                if ext in VIDEO_EXTS:
                    m_type = 'video'
                else:
                    m_type = 'image'
                
                # Debug
                print(f"DEBUG: ไฟล์ {p} (นามสกุล {ext}) ==> {m_type}")

                post.struct_media.append({'path': p, 'type': m_type})
    
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('ชื่อซ้ำครับ')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login Failed')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = current_user.username 
        
        media_paths = []
        if 'file' in request.files:
            files = request.files.getlist('file')
            for file in files:
                if file and allowed_file(file.filename):
                    # --- [แก้ใหม่ตรงนี้: เปลี่ยนชื่อไฟล์เป็นรหัสสุ่ม] ---
                    # 1. หานามสกุลเดิม (.mp4)
                    ext = os.path.splitext(file.filename)[1].lower()
                    
                    # 2. ตั้งชื่อใหม่ด้วย UUID (เช่น a1b2c3d4.mp4)
                    new_filename = f"{uuid.uuid4().hex}{ext}"
                    
                    # 3. บันทึก
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    media_paths.append(f'uploads/{new_filename}')
        
        media_string = ",".join(media_paths)
        thai_time = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")

        new_post = Post(title=title, content=content, author=author, media_list=media_string, timestamp=thai_time)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/status')
def status_check():
    return redirect("https://check-status-final-88358153370.asia-southeast1.run.app")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
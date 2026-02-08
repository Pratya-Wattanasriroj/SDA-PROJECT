import os
import uuid
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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm', 'mkv'}

# --- [ตาราง 1] เก็บความเป็นเพื่อน (Accept แล้ว) ---
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# --- [ตาราง 2] เก็บคำขอติดตาม (Pending Request) ---
class FollowRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # เชื่อมโยงเพื่อให้ดึงข้อมูลง่าย
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    # ความสัมพันธ์เพื่อน (Accept แล้ว)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    # เช็คว่า Follow สำเร็จหรือยัง (เป็นเพื่อนกันยัง)
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    # เช็คว่าเคยส่งคำขอไปหรือยัง (Pending)
    def has_requested(self, user):
        return FollowRequest.query.filter_by(sender_id=self.id, receiver_id=user.id).first() is not None

    # ส่งคำขอ (แทนการ Follow ทันที)
    def send_request(self, user):
        if not self.is_following(user) and not self.has_requested(user):
            req = FollowRequest(sender_id=self.id, receiver_id=user.id)
            db.session.add(req)

    # ยกเลิกคำขอ / หรือเลิกติดตาม
    def unfollow(self, user):
        # 1. ถ้าเป็นเพื่อนแล้ว -> ลบเพื่อน
        if self.is_following(user):
            self.followed.remove(user)
        # 2. ถ้าแค่ส่งคำขอไว้ -> ลบคำขอ
        req = FollowRequest.query.filter_by(sender_id=self.id, receiver_id=user.id).first()
        if req:
            db.session.delete(req)

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
    VIDEO_EXTS = {'mp4', 'mov', 'avi', 'webm', 'mkv'}

    for post in posts:
        post.struct_media = []
        if post.media_list:
            paths = post.media_list.split(',')
            for p in paths:
                p = p.strip()
                if not p: continue
                try:
                    ext = p.split('.')[-1].lower()
                except:
                    ext = ""
                m_type = 'video' if ext in VIDEO_EXTS else 'image'
                post.struct_media.append({'path': p, 'type': m_type})
    
    return render_template('index.html', posts=posts)

# --- [System] จัดการ Request ---

@app.route('/send_request/<username>')
@login_required
def send_request(username):
    target = User.query.filter_by(username=username).first()
    if target and target != current_user:
        current_user.send_request(target)
        db.session.commit()
        flash(f'ส่งคำขอติดตาม {username} แล้ว รอการตอบรับนะ')
    return redirect(request.referrer or url_for('home'))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    target = User.query.filter_by(username=username).first()
    if target:
        current_user.unfollow(target)
        db.session.commit()
        flash(f'ยกเลิกการติดตาม/คำขอ {username} เรียบร้อย')
    return redirect(request.referrer or url_for('home'))

# --- [System] Notifications (หน้าแจ้งเตือน) ---
@app.route('/notifications')
@login_required
def notifications():
    # ดึงคำขอที่มีคนส่งมาหาเรา (receiver = เรา)
    requests = FollowRequest.query.filter_by(receiver_id=current_user.id).all()
    return render_template('notifications.html', requests=requests)

@app.route('/accept/<int:req_id>')
@login_required
def accept_request(req_id):
    req = FollowRequest.query.get_or_404(req_id)
    
    # ความปลอดภัย: เช็คว่าคำขอนี้ส่งมาหาเราจริงๆ ใช่ไหม
    if req.receiver_id != current_user.id:
        return redirect(url_for('home'))
    
    # 1. ให้คนขอ (A) ติดตามเรา (B) -> (A Follow B)
    if not req.sender.is_following(current_user):
        req.sender.followed.append(current_user)

    # 2. [ส่วนที่เพิ่ม] ให้เรา (B) ติดตามคนขอ (A) กลับทันที -> (B Follow A)
    if not current_user.is_following(req.sender):
        current_user.followed.append(req.sender)
    
    # 3. ลบคำขอออกจากระบบ
    db.session.delete(req)
    db.session.commit()
    
    flash(f'คุณกับ {req.sender.username} เป็นเพื่อนกันแล้ว! (ติดตามกันและกัน)')
    return redirect(url_for('notifications'))

@app.route('/reject/<int:req_id>')
@login_required
def reject_request(req_id):
    req = FollowRequest.query.get_or_404(req_id)
    if req.receiver_id == current_user.id:
        db.session.delete(req)
        db.session.commit()
        flash('ปฏิเสธคำขอแล้ว')
    return redirect(url_for('notifications'))

@app.route('/friends')
@login_required
def friends_page():
    following_list = current_user.followed.all()
    return render_template('friends.html', following_list=following_list)

# --- Standard Routes ---

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
                    ext = os.path.splitext(file.filename)[1].lower()
                    new_filename = f"{uuid.uuid4().hex}{ext}"
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
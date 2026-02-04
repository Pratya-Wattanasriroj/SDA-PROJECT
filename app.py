from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# จำลอง Database
posts_db = [
    {
        'id': 1,
        'title': 'ยินดีต้อนรับสู่ Webboard กลุ่มเรา!',
        'author': 'Admin',
        'content': 'พื้นที่นี้ให้เพื่อนๆ มาโพสต์แลกเปลี่ยนความคิดเห็นกันได้เลย',
        'timestamp': '2023-10-27 10:00'
    }
]

@app.route('/')
def home():
    query = request.args.get('q')
    if query:
        # ระบบค้นหาเดิม
        filtered_posts = [p for p in posts_db if query.lower() in p['title'].lower() or query.lower() in p['content'].lower()]
        posts_to_show = filtered_posts
    else:
        posts_to_show = posts_db
    
    return render_template('index.html', posts=reversed(posts_to_show))

# --- [ส่วนที่เพิ่มมาใหม่] หน้า Friends ---
@app.route('/friends')
def friends_page():
    # สร้างข้อมูลจำลองโพสต์ของเพื่อน (หรือจะ Filter จาก Database ก็ได้)
    friend_posts = [
        {
            'id': 99, 
            'title': 'เย็นนี้ใครว่างบ้าง?', 
            'author': 'BestFriend_007', 
            'content': 'ไปกินหมูกระทะหน้าปากซอยกัน หิวมากกก', 
            'timestamp': 'Just Now'
        },
        {
            'id': 98, 
            'title': 'ถามการบ้าน วิชา OS หน่อยครับ', 
            'author': 'StudyBuddy', 
            'content': 'ตรง Docker Compose มันรันไม่ขึ้น มีใครรู้บ้าง', 
            'timestamp': '10 mins ago'
        }
    ]
    # ส่งไปที่ template เดิม แต่ข้อมูลเปลี่ยนไป
    return render_template('index.html', posts=friend_posts)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        new_post = {
            'id': len(posts_db) + 1,
            'title': title,
            'author': author,
            'content': content,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        posts_db.append(new_post)
        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/status')
def status_check():
    # อย่าลืมใส่ลิงก์ Cloud Run ของคุณที่นี่
    CLOUD_FUNCTION_URL = "https://check-status-final-88358153370.asia-southeast1.run.app"
    return redirect(CLOUD_FUNCTION_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
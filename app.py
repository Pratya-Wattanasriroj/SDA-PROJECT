from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# จำลอง Database
posts_db = [
    {
        'id': 1,
        'title': 'ยินดีต้อนรับสู่ Webboard!',
        'author': 'Admin',
        'content': 'โพสต์รูปและวิดีโอได้แล้วนะ ลองดูสิ!',
        'media': 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcG96Y3lmaWZqNmJxcWc0ZDV6bm9uY3F6Z2g0bm14Z2g0bm14Z2g0biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0MYt5jPR6QX5pnqM/giphy.gif',
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
    # หน้าเพื่อน (ตัวอย่าง)
    friend_posts = []
    return render_template('index.html', posts=friend_posts)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        media = request.form['media'] # รับลิงก์รูป/วิดีโอ
        
        # คำนวณเวลาไทย (UTC+7)
        thai_time = datetime.utcnow() + timedelta(hours=7)
        formatted_time = thai_time.strftime("%d/%m/%Y %H:%M")

        new_post = {
            'id': len(posts_db) + 1,
            'title': title,
            'author': author,
            'content': content,
            'media': media,
            'timestamp': formatted_time
        }
        posts_db.append(new_post)
        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/status')
def status_check():
    # ใส่ลิงก์ Cloud Run ของคุณที่นี่
    CLOUD_FUNCTION_URL = "https://check-status-final-88358153370.asia-southeast1.run.app"
    return redirect(CLOUD_FUNCTION_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
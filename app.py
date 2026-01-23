# app.py
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# จำลอง Database เก็บกระทู้ (List of Dictionaries)
# เริ่มต้นมีกระทู้ตัวอย่าง 1 อัน
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
    # ส่งข้อมูลกระทู้ทั้งหมดไปให้หน้าเว็บ (เรียงจากใหม่ไปเก่า)
    return render_template('index.html', posts=reversed(posts_db))

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        # รับค่าจากฟอร์ม
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']
        
        # สร้างกระทู้ใหม่
        new_post = {
            'id': len(posts_db) + 1,
            'title': title,
            'author': author,
            'content': content,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # บันทึกลง "Database"
        posts_db.append(new_post)
        
        return redirect(url_for('home'))
            
    return render_template('create.html')

# เชื่อมต่อกับ Cloud Function (ปุ่มเช็คสถานะ)
@app.route('/status')
def status_check():
    # ใส่ URL Cloud Function ของคุณที่นี่
    CLOUD_FUNCTION_URL = "https://check-status-final-88358153370.asia-southeast1.run.app"
    return redirect(CLOUD_FUNCTION_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
from flask import Flask, render_template, request
import sqlite3
import qrcode
import uuid
import os
import datetime

app = Flask(__name__)

# 🔹 Database initialize
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            token TEXT
        )
    ''')

    conn.commit()
    conn.close()


# 🔹 Home
@app.route('/')
def home():
    return render_template('index.html')


# 🔹 Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return "Registered Successfully ✅"

    return render_template('register.html')


# 🔹 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return "Login Successful ✅"
        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')


# 🔹 Generate QR
@app.route('/generate_qr')
def generate_qr():
    token = str(uuid.uuid4())

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO qr_tokens (token) VALUES (?)", (token,))
    conn.commit()
    conn.close()

    if not os.path.exists('static'):
        os.makedirs('static')

    img = qrcode.make(token)
    img.save("static/qr.png")

    return f"""
    <h2>QR Generated ✅</h2>
    <p>{token}</p>
    <img src='/static/qr.png'>
    <br><br>
    <a href="/scan">Go to Scan Page</a>
    """


# 🔹 Mark Attendance (with time + duplicate check)
@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if request.method == 'POST':
        username = request.form['username']
        token = request.form['token']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT created_at FROM qr_tokens WHERE token=?", (token,))
        data = cursor.fetchone()

        if data:
            created_time = datetime.datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.datetime.now()
            diff = (current_time - created_time).seconds

            if diff > 60:
                conn.close()
                return "QR Expired ❌"

            # 🔥 Duplicate check
            cursor.execute("SELECT * FROM attendance WHERE username=? AND token=?", (username, token))
            already = cursor.fetchone()

            if already:
                conn.close()
                return "Attendance Already Marked ⚠️"

            # Insert attendance
            cursor.execute("INSERT INTO attendance (username, token) VALUES (?, ?)", (username, token))
            conn.commit()
            conn.close()
            return "Attendance Marked ✅"

        else:
            conn.close()
            return "Invalid QR ❌"

    return '''
    <h2>Mark Attendance</h2>
    <form method="POST">
        Username: <input name="username"><br><br>
        Token: <input name="token"><br><br>
        <button>Submit</button>
    </form>
    '''


# 🔹 Scan Page
@app.route('/scan')
def scan():
    return render_template('scan.html')


# 🔹 Run
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
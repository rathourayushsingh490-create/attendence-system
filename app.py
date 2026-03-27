from flask import Flask, render_template, request
import sqlite3
import qrcode
import uuid
import os
import datetime

app = Flask(__name__)

DB_PATH = os.path.join(os.getcwd(), "database.db")

# 🔹 DB setup (auto create every time)
def get_db():
    conn = sqlite3.connect(DB_PATH)
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
    return conn, cursor


# 🔹 Home
@app.route('/')
def home():
    return render_template('index.html')


# 🔹 Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            conn, cursor = get_db()
            cursor.execute("INSERT INTO students (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()

            return "Registered Successfully ✅"
        except Exception as e:
            return f"Error: {str(e)}"


# 🔹 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            conn, cursor = get_db()
            cursor.execute("SELECT * FROM students WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                return "Login Successful ✅"
            else:
                return "Invalid Credentials ❌"
        except Exception as e:
            return f"Error: {str(e)}"


# 🔹 Generate QR
@app.route('/generate_qr')
def generate_qr():
    try:
        token = str(uuid.uuid4())

        conn, cursor = get_db()
        cursor.execute("INSERT INTO qr_tokens (token) VALUES (?)", (token,))
        conn.commit()
        conn.close()

        img = qrcode.make(token)

        static_path = os.path.join(os.getcwd(), "static")
        os.makedirs(static_path, exist_ok=True)

        file_path = os.path.join(static_path, "qr.png")
        img.save(file_path)

        return f"""
        <h2>QR Generated ✅</h2>
        <p>{token}</p>
        <img src='/static/qr.png'>
        <br><br>
        <a href="/scan">Scan QR</a>
        """
    except Exception as e:
        return f"Error: {str(e)}"


# 🔹 Attendance
@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if request.method == 'POST':
        try:
            username = request.form['username']
            token = request.form['token']

            conn, cursor = get_db()

            cursor.execute("SELECT created_at FROM qr_tokens WHERE token=?", (token,))
            data = cursor.fetchone()

            if data:
                created_time = datetime.datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S")
                diff = (datetime.datetime.now() - created_time).seconds

                if diff > 60:
                    return "QR Expired ❌"

                cursor.execute("SELECT * FROM attendance WHERE username=? AND token=?", (username, token))
                if cursor.fetchone():
                    return "Already Marked ⚠️"

                cursor.execute("INSERT INTO attendance (username, token) VALUES (?, ?)", (username, token))
                conn.commit()
                conn.close()

                return "Attendance Marked ✅"
            else:
                return "Invalid QR ❌"

        except Exception as e:
            return f"Error: {str(e)}"

    return '''
    <form method="POST">
        Username: <input name="username"><br>
        Token: <input name="token"><br>
        <button>Submit</button>
    </form>
    '''


# 🔹 Scan
@app.route('/scan')
def scan():
    return render_template('scan.html')


# 🔹 Run
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

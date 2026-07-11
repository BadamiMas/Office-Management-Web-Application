from calendar import month
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from datetime import timedelta, datetime
from flask_wtf.csrf import generate_csrf
import cv2
import numpy as np
import face_recognition
import base64
from Secrefy import EncryptionTool
import os
from face import encodings
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from threading import Thread
import openpyxl
from finance_export import generate_quotation_pdf, generate_invoice_pdf
import json



app = Flask(__name__)
app.secret_key = "icsp"  # needed for session

# Security Config
app.config.update({
    'SESSION_COOKIE_SAMESITE': "None",
    'SESSION_COOKIE_SECURE': True,
    'PERMANENT_SESSION_LIFETIME' : timedelta(minutes=10)
})

# Extensions
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
csrf.init_app(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",       
        password="",       
        database="icsp"  
    )

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    password = request.form['password']

    if not name or not password:
        flash("Please fill in both fields")
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE name=%s", (name,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.check_password_hash(user['password'], password):
        session['user'] = user['name']
        session['role'] = user.get("role", "user")
        session.permanent = True
        _record_login(user['name'])
        print(f"LOGIN RECORDED FOR: {user['name']}")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password")
        return redirect(url_for('home'))


@app.route("/face_login", methods=["POST"])
def face_login():
    data = request.get_json()
    if not data or "image" not in data:
        print("No image received!")   # <-- debug
        return jsonify({"success": False, "message": "No image received"})
    
    print("Image received!")   # <-- debug
    print(data["image"][:50])   # <-- debug

 

    # Decode base64 image from browser
    image_data = data["image"].split(",")[1]
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Detect face
    encodings = face_recognition.face_encodings(frame)
    if len(encodings) == 0:
        return jsonify({"success": False, "message": "No face detected. Try again."})

    current_encoding = encodings[0]

    # Load face encodes from DB
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, role, face_encode FROM users")
    users = cursor.fetchall()
    conn.close()

    for user in users:
        db_encoding = np.frombuffer(base64.b64decode(user["face_encode"]), dtype=np.float64)
        match = face_recognition.compare_faces([db_encoding], current_encoding)[0]
        if match:
            session["user"] = user["name"]
            session["role"] = user.get("role", "user")
            _record_login(user["name"])
            return jsonify({"success": True, "redirect": url_for("dashboard")})

    print(f"Matched user: {user['name']} ({user['role']})")  # <-- debug
    return jsonify({"success": False, "message": "Face not recognized"})

#--------------------------------------------
# DASHBOARD ROUTE WITH ROLE-BASED REDIRECTION
#--------------------------------------------

@app.route('/dashboard')
def dashboard():
    
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', username=session['user'], role=session.get('role', 'user'))
    

# @app.route('/acc_dashboard')
# def acc_dashboard():
#         return render_template('acc_dashboard.html', username=session['user'], role=session.get('role', 'user'))

# @app.route('/head_dashboard')
# def head_dashboard():
#         return render_template('head_dashboard.html', username=session['user'], role=session.get('role', 'user'))

# @app.route('/hr_dashboard')
# def hr_dashboard():
#         return render_template('hr_dashboard.html', username=session['user'], role=session.get('role', 'user'))

#---------------------------------------------
# JOB ROUTE
#---------------------------------------------

@app.route('/job')
def job():
    if 'user' not in session:
        return redirect(url_for('home'))

    role = session.get('role', 'user')
    if role == 'Accountant':
        return redirect(url_for('cashtable'))
    elif role == 'HR':
        return redirect(url_for('jobtable'))
    elif role == 'Head':
        return redirect(url_for('headtable'))
    else:
        return redirect(url_for('jobtable'))


@app.route('/acc_job')
def acc_job():
    return render_template('acc_job.html', username=session['user'], role=session.get('role', 'user'))


@app.route('/hr_job')
def hr_job():
    return render_template('hr_job.html', username=session['user'], role=session.get('role', 'user'))


@app.route('/head_job')
def head_job():
    return render_template('head_job.html', username=session['user'], role=session.get('role', 'user'))


@app.route('/secrefy')
def doc():
    return render_template('doc.html', username=session['user'], role=session.get('role', 'user'))


# HEAD GRAPH

@app.route('/get_total_employees')
def get_total_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return jsonify({'total_employees': total})

@app.route('/get_company_progress')
def get_company_progress():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # --- Get current year and last 6 months range ---
    now = datetime.now()
    start_date = (now.replace(day=1) - timedelta(days=150)).replace(day=1)  # roughly 5 months before
    end_date = now

    # --- Get monthly cash flow (sum of in/out) within last 6 months ---
    cursor.execute("""
        SELECT 
            YEAR(flow_date) AS year,
            MONTH(flow_date) AS month,
            SUM(cash_in) AS total_in,
            SUM(cash_out) AS total_out
        FROM cash_flow
        WHERE flow_date BETWEEN %s AND %s
        GROUP BY YEAR(flow_date), MONTH(flow_date)
        ORDER BY YEAR(flow_date), MONTH(flow_date)
    """, (start_date, end_date))
    cash_data = cursor.fetchall()

    # --- Get employee count by hire month within last 6 months ---
    cursor.execute("""
        SELECT 
            YEAR(date_hired) AS year,
            MONTH(date_hired) AS month,
            COUNT(*) AS total_hired
        FROM employees
        WHERE date_hired BETWEEN %s AND %s
        GROUP BY YEAR(date_hired), MONTH(date_hired)
        ORDER BY YEAR(date_hired), MONTH(date_hired)
    """, (start_date, end_date))
    emp_data = cursor.fetchall()

    cursor.close()
    conn.close()

    # --- Merge data ---
    data_by_month = {}

    for row in cash_data:
        key = (row['year'], row['month'])
        data_by_month[key] = {
            'cash_in': float(row['total_in'] or 0),
            'cash_out': float(row['total_out'] or 0),
            'employees': 0
        }

    for row in emp_data:
        key = (row['year'], row['month'])
        if key not in data_by_month:
            data_by_month[key] = {'cash_in': 0, 'cash_out': 0, 'employees': 0}
        data_by_month[key]['employees'] = row['total_hired']

    formatted = []
    for (year, month) in sorted(data_by_month.keys()):
        if year == now.year:  # only this year
            formatted.append({
                'year': year,
                'month': month,
                'cash_in': data_by_month[(year, month)]['cash_in'],
                'cash_out': data_by_month[(year, month)]['cash_out'],
                'employees': data_by_month[(year, month)]['employees']
            })

    return jsonify(formatted)


# HR GRAPH

@app.route('/get_company_progress_hr')
def get_company_progress_hr():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    now = datetime.now()
    start_date = (now.replace(day=1) - timedelta(days=150)).replace(day=1)  # last 5 months
    end_date = now

    cursor.execute("""
        SELECT 
            YEAR(date_hired) AS year,
            MONTH(date_hired) AS month,
            COUNT(*) AS total_hired
        FROM employees
        WHERE date_hired BETWEEN %s AND %s
        GROUP BY YEAR(date_hired), MONTH(date_hired)
        ORDER BY YEAR(date_hired), MONTH(date_hired)
    """, (start_date, end_date))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # fill missing months with 0
    data_by_month = {}
    for i in range(6):
        month = (start_date + timedelta(days=30*i)).month
        data_by_month[(now.year, month)] = 0

    for row in rows:
        key = (row['year'], row['month'])
        data_by_month[key] = row['total_hired']

    formatted = []
    for (year, month) in sorted(data_by_month.keys()):
        if year == now.year:
            formatted.append({
                'year': year,
                'month': month,
                'employees': data_by_month[(year, month)]
            })

    return jsonify(formatted)


# ACCOUNTANT GRAPH

@app.route('/get_company_progress_acc')
def get_cash_flow():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Last 6 months
    now = datetime.now()
    start_date = (now.replace(day=1) - timedelta(days=150)).replace(day=1)  # roughly 5 months before
    end_date = now

    cursor.execute("""
        SELECT 
            YEAR(flow_date) AS year,
            MONTH(flow_date) AS month,
            SUM(cash_in) AS cash_in,
            SUM(cash_out) AS cash_out
        FROM cash_flow
        WHERE flow_date BETWEEN %s AND %s
        GROUP BY YEAR(flow_date), MONTH(flow_date)
        ORDER BY YEAR(flow_date), MONTH(flow_date)
    """, (start_date, end_date))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Format to return month name + amounts
    data = []
    for row in rows:
        month_name = datetime(row['year'], row['month'], 1).strftime('%b')
        data.append({
            'month': month_name,
            'cash_in': float(row['cash_in'] or 0),
            'cash_out': float(row['cash_out'] or 0)
        })

    return jsonify(data)

# ATTENDANCE

def _record_login(username):
    today = datetime.now().date()
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM attendance WHERE user_name=%s AND date=%s",
            (username, today)
        )
        existing = cursor.fetchone()
        if not existing:
            cursor.execute(
                "INSERT INTO attendance (user_name, login_time, date) VALUES (%s, %s, %s)",
                (username, datetime.now(), today)
            )
            conn.commit()
    finally:
        conn.close()


def _record_logout(username):
    today = datetime.now().date()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance SET logout_time=%s
            WHERE user_name=%s AND date=%s
        """, (datetime.now(), username, today))
        conn.commit()
    finally:
        conn.close()


@app.route('/get_attendance')
def get_attendance():
    if 'user' not in session:
        return jsonify({'login_time': None, 'logout_time': None})
    today = datetime.now().date()
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT login_time, logout_time FROM attendance WHERE user_name=%s AND date=%s",
            (session['user'], today)
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({'login_time': None, 'logout_time': None})

    return jsonify({
        'login_time': row['login_time'].strftime('%I:%M %p') if row['login_time'] else None,
        'logout_time': row['logout_time'].strftime('%I:%M %p') if row['logout_time'] else None
    })


@app.route('/get_all_attendance')
def get_all_attendance():
    if session.get('role') != 'Head':
        return "Access denied", 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_name, date, login_time, logout_time
            FROM attendance
            ORDER BY date DESC, user_name
        """)
        rows = cursor.fetchall()
    finally:
        conn.close()

    for row in rows:
        row['date'] = row['date'].strftime('%d %b %Y')
        row['login_time'] = row['login_time'].strftime('%I:%M %p') if row['login_time'] else '-'
        row['logout_time'] = row['logout_time'].strftime('%I:%M %p') if row['logout_time'] else '-'

    return jsonify(rows)

# SECREFY TKINTER TO FLASK

@app.route("/encrypt", methods=["POST"])
def encrypt_file():
    file = request.files.get("file")
    key = request.form.get("key")
    salt = key[::-1]  # always derive salt from key for simplicity

    if not file or not key:
        flash("File and key are required")
        return redirect(url_for("encrypt_file"))

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    cipher = EncryptionTool(filepath, key, salt)
    for _ in cipher.encrypt():  # run generator
        pass

    return send_file(
        cipher.encrypt_output_file,
        as_attachment=True,
        download_name=os.path.basename(cipher.encrypt_output_file)
    )


@app.route("/decrypt", methods=["POST"])
def decrypt_file():
    file = request.files.get("file")
    key = request.form.get("key")
    salt = key[::-1]  # must be exactly the same as encryption

    if not file or not key:
        flash("File and key are required")
        return redirect(url_for("decrypt_file"))

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    cipher = EncryptionTool(filepath, key, salt)
    for _ in cipher.decrypt():
        pass

    return send_file(
        cipher.decrypt_output_file,
        as_attachment=True,
        download_name=os.path.basename(cipher.decrypt_output_file)
    )


#**************************
# JOB OPERATIONS
#**************************

#-------------------------------
# HR
#-------------------------------

# Google sheets integration

SHEETS_URL = "https://script.google.com/macros/s/AKfycbz3ojA5MP9SsYau46gaYMXfsQGLsz1vvhjGMdwgauMIoNFEWKHjCMh4Y3bEIBMp4tE8/exec"

def sync_to_sheets(action, employee):
    def _sync():

        """Silently syncs employee data to Google Sheets."""
        try:
            requests.post(SHEETS_URL, data={
                'action': action,
                'id': employee.get('id', ''),
                'company_id': employee.get('company_id', ''),
                'name': employee.get('name', ''),
                'age': employee.get('age', ''),
                'city': employee.get('city', ''),
                'email': employee.get('email', ''),
                'number': employee.get('number', ''),
                'role': employee.get('role', ''),
                'date_hired': str(employee.get('date_hired', '')),
                'bank_acc': employee.get('bank_acc', ''),
                'company_code': employee.get('company_code', ''),
                'emp_type': employee.get('emp_type', '')
            }, timeout=15)
        except Exception as e:
            print(f"Sheets sync failed (non-critical): {e}")
    
    Thread(target=_sync, daemon=True).start()

@app.route('/employee')
def jobtable():
    if 'user' not in session:
        return redirect(url_for('home'))

    edit_id        = request.args.get('edit_id')
    company_filter = request.args.get('company_fk', '')

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # companies for dropdown
        cursor.execute("SELECT * FROM companies ORDER BY code")
        company_list = cursor.fetchall()

        # employees — filtered by company if selected
        if company_filter:
            cursor.execute("""
                SELECT e.*, c.name AS company_name, c.code AS company_code
                FROM employees e
                LEFT JOIN companies c ON e.company_fk = c.id
                WHERE e.company_fk = %s
                ORDER BY e.company_id
            """, (company_filter,))
        else:
            cursor.execute("""
                SELECT e.*, c.name AS company_name, c.code AS company_code
                FROM employees e
                LEFT JOIN companies c ON e.company_fk = c.id
                ORDER BY e.company_id
            """)
        employees = cursor.fetchall()

        employee_to_edit = None
        if edit_id:
            cursor.execute("""
                SELECT e.*, c.name AS company_name, c.code AS company_code
                FROM employees e
                LEFT JOIN companies c ON e.company_fk = c.id
                WHERE e.id = %s
            """, (edit_id,))
            employee_to_edit = cursor.fetchone()
    finally:
        conn.close()

    return render_template('job.html',
        username=session['user'],
        role=session.get('role'),
        employees=employees,
        employee_to_edit=employee_to_edit,
        company_list=company_list,
        company_filter=company_filter
    )


@app.route('/upload_employees', methods=['POST'])
def upload_employees():
    if session.get('role') != 'HR':
        return "Access denied", 403

    file = request.files.get('excel_file')
    if not file:
        flash("No file uploaded")
        return redirect(url_for('jobtable'))

    wb = openpyxl.load_workbook(file)
    ws = wb.active

    # build code→id map
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, code FROM companies")
        company_map = {row['code'].upper(): row['id'] for row in cursor.fetchall()}

        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[1]:  # company_id not empty
                rows.append(row)

        cursor2 = conn.cursor()
        cursor2.execute("DELETE FROM payroll")
        cursor2.execute("DELETE FROM employees")

        # Excel columns:
        # 0:id(skip) 1:company_id 2:name 3:age 4:city 5:email
        # 6:number   7:role       8:date_hired 9:bank_acc 10:company_code
        for row in rows:
            code       = str(row[10]).strip().upper() if row[10] else ''
            company_fk = company_map.get(code)
            number   = str(int(float(row[6]))) if row[6] else ''
            bank_acc = str(int(float(row[9]))) if row[9] else ''
            cursor2.execute("""
                INSERT INTO employees
                    (company_id, name, age, city, email, number, role,
                     date_hired, bank_acc, company_fk, emp_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (row[1], row[2], row[3], row[4], row[5],
                  number, row[7], row[8], bank_acc, company_fk, row[11]))
        conn.commit()

        cursor3 = conn.cursor(dictionary=True)
        cursor3.execute("""
            SELECT e.*, c.code as company_code 
            FROM employees e
            LEFT JOIN companies c ON e.company_fk = c.id
        """)
        all_employees = cursor3.fetchall()
    finally:
        conn.close()
    
    sheets_log_action('Import Employees', f"{len(rows)} records replaced")


    def _full_sync():
        try:
            requests.post(SHEETS_URL, data={'action': 'clear'}, timeout=15)
            for emp in all_employees:
                requests.post(SHEETS_URL, data={
                    'action': 'add',
                    'id': emp['id'],
                    'company_id': emp['company_id'],
                    'name': emp['name'],
                    'age': emp['age'],
                    'city': emp['city'],
                    'email': emp['email'],
                    'number': emp['number'],
                    'role': emp['role'],
                    'date_hired': str(emp['date_hired']),
                    'bank_acc': emp['bank_acc'],
                    'company_code': emp['company_code'],
                    'emp_type': emp['emp_type'] or ''
                }, timeout=15)
        except Exception as e:
            print(f"Full sync failed: {e}")

    Thread(target=_full_sync, daemon=True).start()
    flash(f"Successfully imported {len(rows)} employees!")
    return redirect(url_for('jobtable'))

# Add employee
@app.route('/addj', methods=['POST'])
def addj():
    company_id  = request.form['company_id']
    name        = request.form['name']
    age         = request.form['age']
    city        = request.form['city']
    email       = request.form['email']
    number      = request.form['number']
    role        = request.form['role']
    date_hired  = request.form['date_hired']
    bank_acc    = request.form.get('bank_acc', '')
    company_fk  = request.form.get('company_fk') or None
    emp_type    = request.form.get('emp_type', '')

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO employees
                (company_id, name, age, city, email, number, role, date_hired, bank_acc, company_fk, emp_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (company_id, name, age, city, email, number, role, date_hired, bank_acc, company_fk, emp_type))
        conn.commit()
        new_id = cursor.lastrowid

        # look up company code for sheets sync
        company_code = ''
        if company_fk:
            cursor.execute("SELECT code FROM companies WHERE id=%s", (company_fk,))
            row = cursor.fetchone()
            if row:
                company_code = row['code']
    finally:
        conn.close()
    
    sheets_log_action('Add Employee', f"{name} ({company_id})")

    sync_to_sheets('add', {
        'id': new_id, 'company_id': company_id, 'name': name, 'age': age,
        'city': city, 'email': email, 'number': number,
        'role': role, 'date_hired': date_hired, 'bank_acc': bank_acc, 'company_code': company_code, 'emp_type': emp_type
    })
    return redirect(url_for('jobtable'))

# Edit employee
@app.route('/editj/<int:id>', methods=['POST'])
def editj(id):
    company_id  = request.form['company_id']
    name        = request.form['name']
    age         = request.form['age']
    city        = request.form['city']
    email       = request.form['email']
    number      = request.form['number']
    role        = request.form['role']
    date_hired  = request.form['date_hired']
    bank_acc    = request.form.get('bank_acc', '')
    company_fk  = request.form.get('company_fk') or None
    emp_type    = request.form.get('emp_type', '')

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            UPDATE employees
            SET company_id=%s, name=%s, age=%s, city=%s, email=%s, number=%s,
                role=%s, date_hired=%s, bank_acc=%s, company_fk=%s, emp_type=%s
            WHERE id=%s
        """, (company_id, name, age, city, email, number, role, date_hired, bank_acc, company_fk, emp_type, id))
        conn.commit()

        # look up emp type
        cursor.execute("SELECT emp_type FROM employees WHERE id=%s", (id,))
        row = cursor.fetchone()
        emp_type = row['emp_type'] if row else ''

        # look up company code for sheets sync
        company_code = ''
        if company_fk:
            cursor.execute("SELECT code FROM companies WHERE id=%s", (company_fk,))
            row = cursor.fetchone()
            if row:
                company_code = row['code']
    finally:
        conn.close()
    
    sheets_log_action('Edit Employee', f"{name} (ID {id})")

    sync_to_sheets('edit', {
        'id': id, 'company_id': company_id, 'name': name, 'age': age,
        'city': city, 'email': email, 'number': number, 'role': role, 'date_hired': date_hired, 'bank_acc': bank_acc, 'company_code': company_code, 'emp_type': emp_type
    })
    return redirect(url_for('jobtable'))

# Delete employee
@app.route('/deletej/<int:id>', methods=['POST'])
def deletej(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    sheets_log_action('Delete Employee', f"ID {id}")

    sync_to_sheets('delete', {'id': id})

    return redirect(url_for('jobtable'))


#-------------------------------
# ACC
#-------------------------------

# View cash flow table
@app.route('/cashflow')
def cashtable():
    if 'user' not in session:
        return redirect(url_for('home'))

    edit_id = request.args.get('edit_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cash_flow ORDER BY flow_date DESC")
    cash_flows = cursor.fetchall()
    cash_to_edit = None

    if edit_id:
        cursor.execute("SELECT * FROM cash_flow WHERE id=%s", (edit_id,))
        cash_to_edit = cursor.fetchone()

    conn.close()
    return render_template('job.html', username=session['user'], role=session.get('role'), cash_flows=cash_flows, cash_to_edit=cash_to_edit)


# Add cash flow
@app.route('/addc', methods=['POST'])
def addc():
    flow_date = request.form['flow_date']
    cash_in = request.form['cash_in']
    cash_out = request.form['cash_out']
    name = request.form['name']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cash_flow (flow_date, cash_in, cash_out, name)
        VALUES (%s, %s, %s, %s)
    """, (flow_date, cash_in, cash_out, name))
    conn.commit()
    conn.close()
    sheets_log_action('Add Cash Flow', f"{name}")
    return redirect(url_for('cashtable'))


# Edit cash flow
@app.route('/editc/<int:id>', methods=['POST'])
def editc(id):
    flow_date = request.form['flow_date']
    cash_in = request.form['cash_in']
    cash_out = request.form['cash_out']
    name = request.form['name']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cash_flow
        SET flow_date=%s, cash_in=%s, cash_out=%s, name=%s
        WHERE id=%s
    """, (flow_date, cash_in, cash_out, name, id))
    conn.commit()
    conn.close()
    sheets_log_action('Edit Cash Flow', f"ID {id} — {name}")
    return redirect(url_for('cashtable'))


# Delete cash flow
@app.route('/deletec/<int:id>', methods=['POST'])
def deletec(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cash_flow WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    sheets_log_action('Delete Cash Flow', f"ID {id}")
    return redirect(url_for('cashtable'))


# PAYROLL

@app.route('/payroll')
def payrolltable():
    if 'user' not in session:
        return redirect(url_for('home'))
    if session.get('role') != 'Accountant':
        return "Access denied", 403

    setup_id     = request.args.get('setup_id')
    history_month = request.args.get('history_month')
    active_tab   = request.args.get('tab', 'setup')

    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    filter_month  = history_month or current_month

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # all employees for setup tab
        cursor.execute("SELECT * FROM employees ORDER BY company_id")
        employees = cursor.fetchall()

        # employee to setup
        emp_to_setup = None
        if setup_id:
            cursor.execute("SELECT * FROM employees WHERE id=%s", (setup_id,))
            emp_to_setup = cursor.fetchone()
            active_tab = 'setup'

        # payroll history
        cursor.execute("""
            SELECT p.*, e.name, e.company_id, e.emp_type, c.code AS company_code
            FROM payroll p
            JOIN employees e ON p.employee_id = e.id
            LEFT JOIN companies c ON e.company_fk = c.id
            WHERE p.month = %s
            ORDER BY c.code, e.company_id
        """, (filter_month,))
        payroll_history = cursor.fetchall()

    finally:
        conn.close()

    return render_template('payroll.html',
        username=session['user'],
        role=session.get('role'),
        employees=employees,
        emp_to_setup=emp_to_setup,
        payroll_history=payroll_history,
        current_month=current_month,
        history_month=filter_month,
        active_tab=active_tab
    )


@app.route('/setup_employee_pay/<int:id>', methods=['POST'])
def setup_employee_pay(id):
    emp_type = request.form['emp_type']
    base_pay = request.form['base_pay']
    bank_acc = request.form.get('bank_acc', '')

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            UPDATE employees SET emp_type=%s, base_pay=%s, bank_acc=%s WHERE id=%s
        """, (emp_type, base_pay, bank_acc, id))
        conn.commit()

        # fetch details needed for sheets sync
        cursor.execute("""
            SELECT e.*, c.code as company_code
            FROM employees e
            LEFT JOIN companies c ON e.company_fk = c.id
            WHERE e.id=%s
        """, (id,))
        emp = cursor.fetchone()
    finally:
        conn.close()
        sheets_log_action('Setup Pay', f"ID {id} — {emp_type}, base {base_pay}, bank {bank_acc}")


    if emp:
        sync_to_sheets('edit', {
            'id': id,
            'company_id': emp['company_id'],
            'name': emp['name'],
            'age': emp['age'],
            'city': emp['city'],
            'email': emp['email'],
            'number': emp['number'],
            'role': emp['role'],
            'date_hired': str(emp['date_hired']),
            'bank_acc': bank_acc,
            'company_code': emp['company_code'] or '',
            'emp_type': emp_type
        })

    return redirect(url_for('payrolltable'))


@app.route('/get_employees_for_payroll')
def get_employees_for_payroll():
    if session.get('role') != 'Accountant':
        return jsonify([]), 403

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, company_id, name, emp_type, base_pay
            FROM employees
            WHERE emp_type IS NOT NULL AND base_pay IS NOT NULL
            ORDER BY company_id
        """)
        employees = cursor.fetchall()
    finally:
        conn.close()

    # convert Decimal to float for JSON
    for e in employees:
        if e['base_pay']:
            e['base_pay'] = float(e['base_pay'])

    return jsonify(employees)


@app.route('/save_payroll', methods=['POST'])
def save_payroll():
    if session.get('role') != 'Accountant':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    import json as _json
    data    = request.get_json()
    records = data.get('records', [])

    conn = get_db_connection()
    saved = 0
    try:
        cursor = conn.cursor()
        for r in records:
            # upsert — replace existing record for same employee+month
            cursor.execute("""
                INSERT INTO payroll
                    (employee_id, month, gross_pay, cpf_employee, cpf_employer,
                     levy, sdl, overtime_pay, bonus, deductions, net_pay, breakdown)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    gross_pay=VALUES(gross_pay),
                    cpf_employee=VALUES(cpf_employee),
                    cpf_employer=VALUES(cpf_employer),
                    levy=VALUES(levy),
                    sdl=VALUES(sdl),
                    overtime_pay=VALUES(overtime_pay),
                    bonus=VALUES(bonus),
                    deductions=VALUES(deductions),
                    net_pay=VALUES(net_pay),
                    breakdown=VALUES(breakdown)
            """, (
                r['employee_id'], r['month'], r['gross_pay'],
                r['cpf_employee'], r['cpf_employer'], r['levy'], r.get('sdl', 0),
                r['overtime_pay'], r['bonus'], r['deductions'], r['net_pay'],
                _json.dumps(r['breakdown'])
            ))
            saved += 1
        conn.commit()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()
        sheets_log_action('Run Payroll', f"Month {month}, {len(records)} records")

    return jsonify({'success': True, 'saved': saved})


@app.route('/payroll_detail/<int:id>')
def payroll_detail(id):
    if session.get('role') != 'Accountant':
        return "Access denied", 403

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, e.name, e.company_id, e.emp_type
            FROM payroll p
            JOIN employees e ON p.employee_id = e.id
            WHERE p.id = %s
        """, (id,))
        record = cursor.fetchone()
    finally:
        conn.close()

    if not record:
        return "Record not found", 404

    import json as _json
    if record['breakdown']:
        record['breakdown'] = _json.loads(record['breakdown'])

    return render_template('payroll_detail.html',
        username=session['user'],
        role=session.get('role'),
        record=record
    )


@app.route('/delete_payroll/<int:id>', methods=['POST'])
def delete_payroll(id):
    if session.get('role') != 'Accountant':
        return "Access denied", 403

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payroll WHERE id=%s", (id,))
        conn.commit()
    finally:
        conn.close()
        sheets_log_action('Delete Payroll', f"ID {id}")

    return redirect(url_for('payrolltable', tab='history'))


# PAYROLL DOWNLOAD

@app.route('/download_payroll/<fmt>')
def download_payroll(fmt):
    if session.get('role') != 'Accountant':
        return "Access denied", 403

    month = request.args.get('month')
    if not month:
        flash("No month selected")
        return redirect(url_for('payrolltable'))

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.net_pay, e.company_id, e.name, e.bank_acc, e.emp_type,
                   c.id AS cid, c.name AS company_name, c.code AS company_code
            FROM payroll p
            JOIN employees e ON p.employee_id = e.id
            LEFT JOIN companies c ON e.company_fk = c.id
            WHERE p.month = %s
            ORDER BY c.code, e.emp_type, e.company_id
        """, (month,))
        rows = cursor.fetchall()

        cursor.execute("SELECT * FROM companies ORDER BY code")
        all_companies = cursor.fetchall()
    finally:
        conn.close()

    # group by company
    from collections import defaultdict
    fw_types = {'FW'}
    wp_types = {'WP', 'SPASS', 'PR', 'Citizen'}

    by_company = defaultdict(lambda: {'fw': [], 'wp': []})
    for r in rows:
        cid = r['cid'] or 'unassigned'
        if r['emp_type'] in fw_types:
            by_company[cid]['fw'].append(r)
        else:
            by_company[cid]['wp'].append(r)

    companies_data = []
    for co in all_companies:
        grp = by_company.get(co['id'], {'fw': [], 'wp': []})
        companies_data.append({
            'name':         co['name'],
            'code':         co['code'],
            'fw_employees': grp['fw'],
            'wp_employees': grp['wp']
        })

    from payroll_export import generate_payroll_excel, generate_payroll_pdf

    if fmt == 'excel':
        output   = generate_payroll_excel(companies_data, month)
        filename = f"Payroll_{month}.xlsx"
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return send_file(output, as_attachment=True,
                         download_name=filename, mimetype=mimetype)

    elif fmt == 'pdf':
        output   = generate_payroll_pdf(companies_data, month)
        filename = f"Payroll_{month}.pdf"
        return send_file(output, as_attachment=True,
                         download_name=filename, mimetype='application/pdf')

    return "Invalid format", 400


#-------------------------------
# FINANCE
#-------------------------------
FINANCE_COMPANIES = ['TQS', 'TQB', 'TQEA', 'TGC', 'APJ']

# ── QUOTATIONS AND INVOICES ──
 
@app.route('/quotations')
def quotations():
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
 
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        company_filter = request.args.get('company_filter', '')
        status_filter  = request.args.get('status_filter', '')
        edit_id        = request.args.get('edit_id')
        quote_to_edit  = None
 
        query  = "SELECT * FROM quotations WHERE 1=1"
        params = []
        if company_filter:
            query += " AND company_code=%s"; params.append(company_filter)
        if status_filter:
            query += " AND status=%s"; params.append(status_filter)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        quote_list = cursor.fetchall()
 
        if edit_id:
            cursor.execute("SELECT * FROM quotations WHERE id=%s", (edit_id,))
            quote_to_edit = cursor.fetchone()
            if quote_to_edit and isinstance(quote_to_edit.get('line_items'), str):
                quote_to_edit['line_items'] = json.loads(quote_to_edit['line_items'] or '[]')
    finally:
        conn.close()
 
    return render_template('job.html',
        username=session['user'], role=session.get('role'),
        quote_list=quote_list, quote_to_edit=quote_to_edit,
        company_filter=company_filter, status_filter=status_filter,
        companies=FINANCE_COMPANIES, page='quotations')
 
 
@app.route('/add_quotation', methods=['POST'])
def add_quotation():
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
 
    quote_type = request.form.get('quote_type', 'manpower')
    line_items = '[]'
    if quote_type == 'lineitems':
        descs  = request.form.getlist('li_desc[]')
        qtys   = request.form.getlist('li_qty[]')
        rates  = request.form.getlist('li_rate[]')
        items  = []
        for d, q, r in zip(descs, qtys, rates):
            if d.strip():
                items.append({'description': d, 'qty': q, 'rate': r})
        line_items = json.dumps(items)
 
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quotations
            (ref_no, company_code, quote_type, quote_date,
             client_name, client_address, client_attn, client_email, client_tel, client_fax,
             subject, intro, rate_per_hour, line_items,
             notes, terms, client_approver_name, client_approver_designation,
             client_approver_hp, status, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form.get('ref_no'),
            request.form.get('company_code'),
            quote_type,
            request.form.get('quote_date'),
            request.form.get('client_name'),
            request.form.get('client_address'),
            request.form.get('client_attn'),
            request.form.get('client_email'),
            request.form.get('client_tel'),
            request.form.get('client_fax'),
            request.form.get('subject'),
            request.form.get('intro'),
            request.form.get('rate_per_hour') or None,
            line_items,
            request.form.get('notes'),
            request.form.get('terms'),
            request.form.get('client_approver_name'),
            request.form.get('client_approver_designation'),
            request.form.get('client_approver_hp'),
            request.form.get('status', 'draft'),
            session.get('user'),
        ))
        conn.commit()
        sheets_log_action('Add Quotation', f"Ref: {request.form.get('ref_no')} — {request.form.get('client_name')}")
    finally:
        conn.close()
    flash("Quotation added!")
    return redirect(url_for('quotations'))
 
 
@app.route('/edit_quotation/<int:id>', methods=['POST'])
def edit_quotation(id):
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
 
    quote_type = request.form.get('quote_type', 'manpower')
    line_items = '[]'
    if quote_type == 'lineitems':
        descs = request.form.getlist('li_desc[]')
        qtys  = request.form.getlist('li_qty[]')
        rates = request.form.getlist('li_rate[]')
        items = []
        for d, q, r in zip(descs, qtys, rates):
            if d.strip():
                items.append({'description': d, 'qty': q, 'rate': r})
        line_items = json.dumps(items)
 
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE quotations SET
            ref_no=%s, company_code=%s, quote_type=%s, quote_date=%s,
            client_name=%s, client_address=%s, client_attn=%s, client_email=%s,
            client_tel=%s, client_fax=%s, subject=%s, intro=%s,
            rate_per_hour=%s, line_items=%s, notes=%s, terms=%s,
            client_approver_name=%s, client_approver_designation=%s,
            client_approver_hp=%s, status=%s
            WHERE id=%s
        """, (
            request.form.get('ref_no'),
            request.form.get('company_code'),
            quote_type,
            request.form.get('quote_date'),
            request.form.get('client_name'),
            request.form.get('client_address'),
            request.form.get('client_attn'),
            request.form.get('client_email'),
            request.form.get('client_tel'),
            request.form.get('client_fax'),
            request.form.get('subject'),
            request.form.get('intro'),
            request.form.get('rate_per_hour') or None,
            line_items,
            request.form.get('notes'),
            request.form.get('terms'),
            request.form.get('client_approver_name'),
            request.form.get('client_approver_designation'),
            request.form.get('client_approver_hp'),
            request.form.get('status', 'draft'),
            id,
        ))
        conn.commit()
        sheets_log_action('Edit Quotation', f"ID {id} — {request.form.get('ref_no')}")
    finally:
        conn.close()
    return redirect(url_for('quotations'))
 
 
@app.route('/delete_quotation/<int:id>', methods=['POST'])
def delete_quotation(id):
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quotations WHERE id=%s", (id,))
        conn.commit()
        sheets_log_action('Delete Quotation', f"ID {id}")
    finally:
        conn.close()
    return redirect(url_for('quotations'))
 
 
@app.route('/download_quotation/<int:id>')
def download_quotation(id):
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quotations WHERE id=%s", (id,))
        q = cursor.fetchone()
    finally:
        conn.close()
    if not q:
        flash("Quotation not found")
        return redirect(url_for('quotations'))
    if isinstance(q.get('line_items'), str):
        q['line_items'] = json.loads(q['line_items'] or '[]')
    if q.get('quote_date'):
        q['quote_date'] = q['quote_date'].strftime('%d/%m/%Y')
    pdf = generate_quotation_pdf(q)
    filename = f"Quotation_{q.get('ref_no','').replace('/','_')}.pdf"
    return send_file(pdf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)
 
 
@app.route('/quotation_to_invoice/<int:id>')
def quotation_to_invoice(id):
    """Pre-fills invoice form from an approved quotation."""
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quotations WHERE id=%s", (id,))
        q = cursor.fetchone()
    finally:
        conn.close()
    if not q:
        return redirect(url_for('quotations'))
    return redirect(url_for('invoices', from_quote=id))
 
 
# ─── INVOICES ─────────────────────────────────────────────────
 
@app.route('/invoices')
def invoices():
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
 
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        company_filter = request.args.get('company_filter', '')
        status_filter  = request.args.get('status_filter', '')
        edit_id        = request.args.get('edit_id')
        from_quote     = request.args.get('from_quote')
        inv_to_edit    = None
        prefill        = None
 
        query  = "SELECT * FROM invoices WHERE 1=1"
        params = []
        if company_filter:
            query += " AND company_code=%s"; params.append(company_filter)
        if status_filter:
            query += " AND status=%s"; params.append(status_filter)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        inv_list = cursor.fetchall()
 
        if edit_id:
            cursor.execute("SELECT * FROM invoices WHERE id=%s", (edit_id,))
            inv_to_edit = cursor.fetchone()
            if inv_to_edit and isinstance(inv_to_edit.get('line_items'), str):
                inv_to_edit['line_items'] = json.loads(inv_to_edit['line_items'] or '[]')
 
        if from_quote:
            cursor.execute("SELECT * FROM quotations WHERE id=%s", (from_quote,))
            q = cursor.fetchone()
            if q:
                prefill = {
                    'company_code': q['company_code'],
                    'client_name':  q['client_name'],
                    'client_address': q['client_address'],
                    'client_attn':  q['client_attn'],
                    'line_items':   json.loads(q.get('line_items') or '[]'),
                    'quotation_id': q['id'],
                }
    finally:
        conn.close()
 
    return render_template('job.html',
        username=session['user'], role=session.get('role'),
        inv_list=inv_list, inv_to_edit=inv_to_edit, prefill=prefill,
        company_filter=company_filter, status_filter=status_filter,
        companies=FINANCE_COMPANIES, page='invoices')
 
 
@app.route('/add_invoice', methods=['POST'])
def add_invoice():
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
 
    descs = request.form.getlist('li_desc[]')
    qtys  = request.form.getlist('li_qty[]')
    rates = request.form.getlist('li_rate[]')
    items = []
    subtotal = 0
    for d, q, r in zip(descs, qtys, rates):
        if d.strip():
            amt = float(q or 0) * float(r or 0)
            subtotal += amt
            items.append({'description': d, 'qty': q, 'rate': r})
 
    gst_amt     = subtotal * 0.09
    total_claim = subtotal + gst_amt
 
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices
            (invoice_no, company_code, invoice_date, currency,
             client_name, client_address, client_attn,
             work_order, vessel, item_no, yard,
             line_items, subtotal, gst_amount, total_claim,
             closing_note, status, quotation_id, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form.get('invoice_no'),
            request.form.get('company_code'),
            request.form.get('invoice_date'),
            request.form.get('currency', 'SGD'),
            request.form.get('client_name'),
            request.form.get('client_address'),
            request.form.get('client_attn'),
            request.form.get('work_order'),
            request.form.get('vessel'),
            request.form.get('item_no'),
            request.form.get('yard'),
            json.dumps(items),
            subtotal,
            gst_amt,
            total_claim,
            request.form.get('closing_note'),
            request.form.get('status', 'unpaid'),
            request.form.get('quotation_id') or None,
            session.get('user'),
        ))
        conn.commit()
        sheets_log_action('Add Invoice', f"No: {request.form.get('invoice_no')} — {request.form.get('client_name')}")
    finally:
        conn.close()
    flash("Invoice added!")
    return redirect(url_for('invoices'))
 
 
@app.route('/edit_invoice/<int:id>', methods=['POST'])
def edit_invoice(id):
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
 
    descs = request.form.getlist('li_desc[]')
    qtys  = request.form.getlist('li_qty[]')
    rates = request.form.getlist('li_rate[]')
    items = []
    subtotal = 0
    for d, q, r in zip(descs, qtys, rates):
        if d.strip():
            amt = float(q or 0) * float(r or 0)
            subtotal += amt
            items.append({'description': d, 'qty': q, 'rate': r})
 
    gst_amt     = subtotal * 0.09
    total_claim = subtotal + gst_amt
 
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE invoices SET
            invoice_no=%s, company_code=%s, invoice_date=%s, currency=%s,
            client_name=%s, client_address=%s, client_attn=%s,
            work_order=%s, vessel=%s, item_no=%s, yard=%s,
            line_items=%s, subtotal=%s, gst_amount=%s, total_claim=%s,
            closing_note=%s, status=%s
            WHERE id=%s
        """, (
            request.form.get('invoice_no'),
            request.form.get('company_code'),
            request.form.get('invoice_date'),
            request.form.get('currency', 'SGD'),
            request.form.get('client_name'),
            request.form.get('client_address'),
            request.form.get('client_attn'),
            request.form.get('work_order'),
            request.form.get('vessel'),
            request.form.get('item_no'),
            request.form.get('yard'),
            json.dumps(items),
            subtotal, gst_amt, total_claim,
            request.form.get('closing_note'),
            request.form.get('status', 'unpaid'),
            id,
        ))
        conn.commit()
        sheets_log_action('Edit Invoice', f"ID {id} — {request.form.get('invoice_no')}")
    finally:
        conn.close()
    return redirect(url_for('invoices'))
 
 
@app.route('/delete_invoice/<int:id>', methods=['POST'])
def delete_invoice(id):
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE id=%s", (id,))
        conn.commit()
        sheets_log_action('Delete Invoice', f"ID {id}")
    finally:
        conn.close()
    return redirect(url_for('invoices'))
 
 
@app.route('/update_invoice_status/<int:id>', methods=['POST'])
def update_invoice_status(id):
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
    status = request.form.get('status')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE invoices SET status=%s WHERE id=%s", (status, id))
        conn.commit()
        sheets_log_action('Update Invoice Status', f"ID {id} → {status}")
    finally:
        conn.close()
    return redirect(url_for('invoices'))
 
 
@app.route('/download_invoice/<int:id>')
def download_invoice(id):
    if session.get('role') not in ['Finance', 'Head']:
        return "Access denied", 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM invoices WHERE id=%s", (id,))
        inv = cursor.fetchone()
    finally:
        conn.close()
    if not inv:
        flash("Invoice not found")
        return redirect(url_for('invoices'))
    if isinstance(inv.get('line_items'), str):
        inv['line_items'] = json.loads(inv['line_items'] or '[]')
    if inv.get('invoice_date'):
        inv['invoice_date'] = inv['invoice_date'].strftime('%d/%m/%Y')
    pdf = generate_invoice_pdf(inv)
    filename = f"Invoice_{inv.get('invoice_no','').replace('/','_')}.pdf"
    return send_file(pdf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)

#------------------------------- 
# HEAD
#-------------------------------

# View all Head users
@app.route('/users')
def headtable():
    if 'user' not in session:
        return redirect(url_for('home'))

    edit_id = request.args.get('edit_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    users = cursor.fetchall()
    user_to_edit = None

    if edit_id:
        cursor.execute("SELECT * FROM users WHERE id=%s", (edit_id,))
        user_to_edit = cursor.fetchone()

    # Attach plain-text display passwords from session
    display_pw_dict = session.get('display_passwords', {})
    for u in users:
        u["display_password"] = display_pw_dict.get(u["name"], "••••••")  # hide hashed value visually

    conn.close()
    return render_template('job.html', username=session['user'], role=session.get('role'), users=users, user_to_edit=user_to_edit)


# Add Head user
@app.route('/addh', methods=['POST'])
def addh():
    name = request.form['name']
    display_password = request.form['password']
    role = request.form['role']
    image_file = request.files['face_image']  # face image input

    
    # Hash the password
    hashed_pw = bcrypt.generate_password_hash(display_password).decode('utf-8')

    # Save temporarily to get encoding
    image_path = f"temp/{image_file.filename}"
    image_file.save(image_path)

    face_encode_b64 = encodings(image_path)
    if not face_encode_b64:
        return "No face detected in the image.", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, password, role, face_encode)
        VALUES (%s, %s, %s, %s)
    """, (name, hashed_pw, role, face_encode_b64))
    conn.commit()
    conn.close()

    return redirect(url_for('headtable'))


# Edit Head user
@app.route('/edith/<int:id>', methods=['POST'])
def edith(id):
    name = request.form['name']
    password = request.form['password']
    role = request.form['role']
    image_file = request.files.get('face_image')  # optional, may not upload new image

    # Hash the password
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    conn = get_db_connection()
    cursor = conn.cursor()

    if image_file and image_file.filename != "":
        image_path = f"temp/{image_file.filename}"
        image_file.save(image_path)
        face_encode_b64 = encodings(image_path)
        cursor.execute("""
            UPDATE users
            SET name=%s, password=%s, role=%s, face_encode=%s
            WHERE id=%s
        """, (name, hashed_pw, role, face_encode_b64, id))
    else:
        cursor.execute("""
            UPDATE users
            SET name=%s, password=%s, role=%s
            WHERE id=%s
        """, (name, hashed_pw, role, id))

    conn.commit()
    conn.close()
    return redirect(url_for('headtable'))


# Delete Head user
@app.route('/deleteh/<int:id>', methods=['POST'])
def deleteh(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('headtable'))


# COMPANY Naming

@app.route('/companies')
def companies():
    if 'user' not in session:
        return redirect(url_for('home'))
    if session.get('role') not in ['Head', 'HR']:
        return "Access denied", 403

    edit_id = request.args.get('edit_id')
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM companies ORDER BY code")
        company_list = cursor.fetchall()
        company_to_edit = None
        if edit_id:
            cursor.execute("SELECT * FROM companies WHERE id=%s", (edit_id,))
            company_to_edit = cursor.fetchone()
    finally:
        conn.close()

    return render_template('companies.html',
        username=session['user'],
        role=session.get('role'),
        company_list=company_list,
        company_to_edit=company_to_edit
    )


@app.route('/add_company', methods=['POST'])
def add_company():
    if session.get('role') not in ['Head', 'HR']:
        return "Access denied", 403
    name = request.form['name']
    code = request.form['code'].upper()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO companies (name, code) VALUES (%s, %s)", (name, code))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('companies'))


@app.route('/edit_company/<int:id>', methods=['POST'])
def edit_company(id):
    if session.get('role') not in ['Head', 'HR']:
        return "Access denied", 403
    name = request.form['name']
    code = request.form['code'].upper()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE companies SET name=%s, code=%s WHERE id=%s", (name, code, id))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('companies'))


@app.route('/delete_company/<int:id>', methods=['POST'])
def delete_company(id):
    if session.get('role') not in ['Head', 'HR']:
        return "Access denied", 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM companies WHERE id=%s", (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('companies'))


# API — for HR dropdown when adding/editing employees
@app.route('/get_companies')
def get_companies():
    if 'user' not in session:
        return jsonify([])
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, code FROM companies ORDER BY code")
        rows = cursor.fetchall()
    finally:
        conn.close()
    return jsonify(rows)


def sheets_log_action(action, detail=''):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sheet_logs (user, role, action, detail)
            VALUES (%s, %s, %s, %s)
        """, (session.get('user'), session.get('role'), action, detail))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log failed: {e}")

@app.route('/sheet_logs')
def sheet_logs():
    if session.get('role') != 'Head':
        return "Access denied", 403
    role_filter = request.args.get('role_filter', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if role_filter:
        cursor.execute("SELECT * FROM sheet_logs WHERE role=%s ORDER BY created_at DESC", (role_filter,))
    else:
        cursor.execute("SELECT * FROM sheet_logs ORDER BY created_at DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template('logs.html', username=session['user'], role=session.get('role'),
                           logs=logs, role_filter=role_filter)

@app.route('/clear_sheet_logs', methods=['POST'])
def clear_sheet_logs():
    if session.get('role') != 'Head':
        return "Access denied", 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sheet_logs")
    conn.commit()
    conn.close()
    return redirect(url_for('sheet_logs'))



#****************
# LOGOUT ROUTE #
#****************
@app.route('/logout')
def logout():
    if 'user' in session:
        _record_logout(session['user'])
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)



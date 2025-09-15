from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'  # 👈 CHANGE THIS IN PRODUCTION!

# Database connection helper - Returns connection only
def get_db_connection():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    return conn

# Home route - redirect to login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Login Route - Handles both admin and student login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if user is admin
        cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
        admin = cursor.fetchone()

        if admin and check_password_hash(admin['password'], password):
            session['logged_in'] = True
            session['role'] = 'admin'
            session['user_id'] = admin['admin_id']
            session['username'] = admin['username']
            flash('Admin login successful!', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('admin_dashboard'))

        # Check if user is student
        cursor.execute("SELECT * FROM students WHERE username = %s", (username,))
        student = cursor.fetchone()

        if student and check_password_hash(student['password'], password):
            session['logged_in'] = True
            session['role'] = 'student'
            session['user_id'] = student['student_id']
            session['username'] = student['username']
            flash('Student login successful!', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('student_dashboard', id=student['student_id']))

        # Invalid credentials
        flash('Invalid username or password.', 'danger')
        cursor.close()
        conn.close()

    return render_template('login.html')

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Access denied. Please log in as admin.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students ORDER BY name")
    students = cursor.fetchall()
    cursor.execute("SELECT * FROM courses ORDER BY course_id")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html', students=students, courses=courses)

# Student Dashboard
@app.route('/student/dashboard/<int:id>')
def student_dashboard(id):
    if not session.get('logged_in') or session.get('role') != 'student' or session.get('user_id') != id:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get student profile
    cursor.execute("SELECT * FROM students WHERE student_id = %s", (id,))
    student = cursor.fetchone()

    # Get enrolled courses and marks
    cursor.execute("""
        SELECT c.course_id, c.course_name, c.credits, m.marks 
        FROM student_courses sc
        JOIN courses c ON sc.course_id = c.course_id
        LEFT JOIN marks m ON sc.student_id = m.student_id AND sc.course_id = m.course_id
        WHERE sc.student_id = %s
    """, (id,))
    enrollments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student_dashboard.html', student=student, enrollments=enrollments)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- ADMIN CRUD OPERATIONS ---

# Add Student
@app.route('/add_student', methods=['POST'])
def add_student():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    data = request.form
    hashed_pw = generate_password_hash(data['password'])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO students (username, password, name, dob, department, year, email, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['username'],
            hashed_pw,
            data['name'],
            data['dob'],
            data['department'],
            int(data['year']),
            data['email'],
            data['phone']
        ))
        conn.commit()
        flash('Student added successfully!', 'success')
    except mysql.connector.IntegrityError as e:
        flash('Username or email already exists.', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

# Edit Student
@app.route('/edit_student/<int:id>', methods=['POST'])
def edit_student(id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    data = request.form
    hashed_pw = generate_password_hash(data['password']) if data['password'] else None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if hashed_pw:
        cursor.execute("""
            UPDATE students 
            SET username=%s, password=%s, name=%s, dob=%s, department=%s, year=%s, email=%s, phone=%s 
            WHERE student_id=%s
        """, (
            data['username'],
            hashed_pw,
            data['name'],
            data['dob'],
            data['department'],
            int(data['year']),
            data['email'],
            data['phone'],
            id
        ))
    else:
        cursor.execute("""
            UPDATE students 
            SET username=%s, name=%s, dob=%s, department=%s, year=%s, email=%s, phone=%s 
            WHERE student_id=%s
        """, (
            data['username'],
            data['name'],
            data['dob'],
            data['department'],
            int(data['year']),
            data['email'],
            data['phone'],
            id
        ))

    conn.commit()
    cursor.close()
    conn.close()

    flash('Student updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Delete Student
@app.route('/delete_student/<int:id>')
def delete_student(id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM students WHERE student_id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Student deleted successfully!', 'warning')
    return redirect(url_for('admin_dashboard'))

# Add Course
@app.route('/add_course', methods=['POST'])
def add_course():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO courses (course_id, course_name, credits) 
            VALUES (%s, %s, %s)
        """, (data['course_id'], data['course_name'], int(data['credits'])))
        conn.commit()
        flash('Course added successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('Course ID already exists.', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

# Assign Course to Student
@app.route('/assign_course', methods=['POST'])
def assign_course():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO student_courses (student_id, course_id) 
            VALUES (%s, %s)
        """, (int(data['student_id']), data['course_id']))
        conn.commit()
        flash('Course assigned successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('Student is already enrolled in this course or does not exist.', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

# Add Marks
@app.route('/add_marks', methods=['POST'])
def add_marks():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO marks (student_id, course_id, marks) 
            VALUES (%s, %s, %s)
        """, (int(data['student_id']), data['course_id'], float(data['marks'])))
        conn.commit()
        flash('Marks added successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('Marks for this student-course already exist.', 'danger')
    except ValueError:
        flash('Invalid marks value.', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'  # 👈 CHANGE THIS IN PRODUCTION!

# Database connection helper - Returns connection only
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='kidflash',  # 🔐 YOUR REAL MYSQL PASSWORD
        database='student_db'
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
        password = request.form['password'].encode('utf-8')  # Encode for bcrypt

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if user is admin
        cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
        admin = cursor.fetchone()

        if admin:
            stored_hash = admin['password'].encode('utf-8')
            if bcrypt.checkpw(password, stored_hash):
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

        if student:
            stored_hash = student['password'].encode('utf-8')
            if bcrypt.checkpw(password, stored_hash):
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
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8') if data['password'] else None

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

# MARK ATTENDANCE ROUTE — THIS IS THE KEY ONE YOU HAVE
@app.route('/admin/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Access denied. Please log in as admin.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        selected_course_id = request.form.get('course_id')
        selected_date = request.form.get('date')

        if not selected_course_id or not selected_date:
            flash('Please select a course and a date.', 'warning')
            cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_id")
            courses = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('admin_mark_attendance.html', courses=courses, selected_course="", selected_date="", students=[])

        # Fetch students enrolled in the selected course
        cursor.execute("""
            SELECT s.student_id, s.name, s.username
            FROM students s
            JOIN student_courses sc ON s.student_id = sc.student_id
            WHERE sc.course_id = %s
            ORDER BY s.name
        """, (selected_course_id,))
        students_in_course = cursor.fetchall()

        # Check existing attendance records for this course/date
        existing_attendance = {}
        if students_in_course:
            student_ids = [str(s['student_id']) for s in students_in_course]
            format_strings = ','.join(['%s'] * len(student_ids))
            query = f"SELECT student_id, status, notes FROM attendance WHERE course_id = %s AND date = %s AND student_id IN ({format_strings})"
            params = [selected_course_id, selected_date] + student_ids
            cursor.execute(query, params)
            existing_records = cursor.fetchall()
            for record in existing_records:
                existing_attendance[record['student_id']] = {'status': record['status'], 'notes': record['notes']}

        # Process submitted attendance data
        submitted_attendance = request.form.to_dict(flat=False)

        try:
            for student in students_in_course:
                student_id = student['student_id']
                key_status = f"attendance[{student_id}][status]"
                key_notes = f"attendance[{student_id}][notes]"

                status_list = submitted_attendance.get(key_status, ['Present'])
                notes_list = submitted_attendance.get(key_notes, [''])

                status = status_list[0] if status_list else 'Present'
                notes = notes_list[0] if notes_list else ''

                if student_id in existing_attendance:
                    cursor.execute("""
                        UPDATE attendance
                        SET status = %s, notes = %s
                        WHERE student_id = %s AND course_id = %s AND date = %s
                    """, (status, notes, student_id, selected_course_id, selected_date))
                else:
                    cursor.execute("""
                        INSERT INTO attendance (student_id, course_id, date, status, notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (student_id, selected_course_id, selected_date, status, notes))

            conn.commit()
            flash(f'Attendance marked successfully for course {selected_course_id} on {selected_date}.', 'success')
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f'Error saving attendance: {err}', 'danger')

        # Re-fetch courses and students to re-render form
        cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_id")
        courses = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_mark_attendance.html', courses=courses, selected_course=selected_course_id, selected_date=selected_date, students=students_in_course, existing_attendance=existing_attendance)

    # Handle GET request: Show empty form
    cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_id")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_mark_attendance.html', courses=courses, selected_course="", selected_date="", students=[])

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
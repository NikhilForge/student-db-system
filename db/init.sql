-- Database initialization for student-db-system
CREATE DATABASE IF NOT EXISTS student_db;
USE student_db;

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    dob DATE,
    department VARCHAR(100),
    year INT,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50)
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR(50) PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    credits INT
);

-- Student-Courses join table
CREATE TABLE IF NOT EXISTS student_courses (
    student_id INT,
    course_id VARCHAR(50),
    PRIMARY KEY(student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

-- Marks table
CREATE TABLE IF NOT EXISTS marks (
    student_id INT,
    course_id VARCHAR(50),
    marks FLOAT,
    PRIMARY KEY(student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

-- Placeholder admin user - replace <HASHED_PASSWORD> below
INSERT INTO admin (username, password) VALUES ('admin', 'pbkdf2:sha256:600000$Qxdm6jfP9n1GzXC4$bff18f78d600f6f7724da57870d893e65620998203322dd8593c6e6c00978e59')
ON DUPLICATE KEY UPDATE password = VALUES(password);

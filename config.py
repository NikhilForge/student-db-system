# config.py
import os

MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'yourpassword')
MYSQL_DB = os.getenv('MYSQL_DB', 'student_db')
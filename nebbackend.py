from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS  # Import the CORS class
from sqlalchemy import func

app = Flask(_name_)
CORS(app)  # Enable CORS for all routes
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/nebula'
db = SQLAlchemy(app)

# Define the database model with explicit table name
class Student(db.Model):
    _tablename_ = 'students'  # Explicitly specify the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    attendance_average = db.Column(db.DECIMAL(5, 2), nullable=False)
    assignment_completion = db.Column(db.Integer, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    cohort = db.Column(db.String(255), nullable=False)

# Define the database model for weekly attendance
class WeeklyAttendance(db.Model):
    _tablename_ = 'weekly_attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    week = db.Column(db.String(255), nullable=False)
    present = db.Column(db.Integer, nullable=False)
    absent = db.Column(db.Integer, nullable=False)

# Health check endpoint
@app.route('/api/health-check', methods=['GET'])
def health_check():
    # Perform any health check logic here
    # For example, check database connectivity, external service availability, etc.
    
    # Return a simple health check response
    return 'Service is healthy'

# API endpoint to get all students
@app.route('/api/students', methods=['GET'])
def get_all_students():
    students = Student.query.all()
    student_list = []
    for student in students:
        student_data = {
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'attendance_average': float(student.attendance_average),
            'assignment_completion': student.assignment_completion,
            'ranking': student.ranking,
            'cohort': student.cohort
        }
        student_list.append(student_data)
    return jsonify(student_list)  # Return the list of student data directly

# Route to get a student's details by email
@app.route('/api/student/<email>', methods=['POST'])
def get_student_details(email):
    if request.method == 'POST':
        # Retrieve the student details based on the provided email
        student = Student.query.filter_by(email=email).first()

        if student:
            # Construct the student's details as a dictionary
            student_data = {
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'attendance_average': float(student.attendance_average),
                'assignment_completion': student.assignment_completion,
                'ranking': student.ranking,
                'cohort': student.cohort
            }
            return jsonify(student=student_data)
        else:
            return 'Student not found', 404
    else:
        return 'Method not allowed', 405
    

# Route to get cohort statistics by cohort name
@app.route('/api/cohort/stats/<cohort_name>', methods=['GET'])
def get_cohort_stats(cohort_name):
    # Query the database to retrieve attendance data for the specified cohort
    students_in_cohort = Student.query.filter_by(cohort=cohort_name).all()

    if students_in_cohort:
        total_students = len(students_in_cohort)
        total_attendance = sum(student.attendance_average for student in students_in_cohort)
        total_assignment_completion = sum(student.assignment_completion for student in students_in_cohort)

        # Calculate average attendance and average assignment completion
        average_attendance = total_attendance / total_students
        average_assignment_completion = total_assignment_completion / total_students

        # Construct the cohort statistics as a dictionary
        cohort_stats = {
            'cohort_name': cohort_name,
            'total_students': total_students,
            'attendance_average': round(average_attendance, 2),
            'assignment_completion': round(average_assignment_completion, 2),
            'top_performer': max(students_in_cohort, key=lambda student: student.attendance_average).name,
            'top_performer_attendance': max(student.attendance_average for student in students_in_cohort)
            # Add more statistics as needed
        }

        # Return the cohort statistics as JSON
        return jsonify(cohort_stats)
    else:
        return 'Cohort not found', 404
    
# Route to get cohort attendance statistics by cohort name
@app.route('/api/cohort/attendance/<cohort_name>', methods=['GET'])
def get_cohort_attendance(cohort_name):
    # Query the database to retrieve weekly attendance data for the specified cohort
    attendance_data = db.session.query(WeeklyAttendance.week, func.sum(WeeklyAttendance.present).label('present'), func.sum(WeeklyAttendance.absent).label('absent')) \
                                .join(Student, Student.id == WeeklyAttendance.student_id) \
                                .filter(Student.cohort == cohort_name) \
                                .group_by(WeeklyAttendance.week) \
                                .all()

    if attendance_data:
        # Calculate attendance statistics for each week
        cohort_attendance = [{'week': week, 'attendanceAverage': (present / (present + absent)) * 100} for week, present, absent in attendance_data]

        # Return the cohort attendance statistics as JSON
        return jsonify(cohort_attendance)
    else:
        return jsonify([])  # Return an empty list if no data found for the cohort

# Route for testing the database connection
@app.route('/api/test-db-connection', methods=['GET', 'POST'])
def test_db_connection():
    if request.method == 'GET':
        try:
            # Perform a simple query to test the database connection
            result = db.session.execute(text('SELECT 1'))
            return 'Database connection is working'
        except Exception as e:
            return f'Database connection error: {str(e)}'
    elif request.method == 'POST':
        # Handle POST request logic here
        # ...
        return 'Database connection is working and Received a POST request'
    else:
        return 'Method not allowed'

if _name_ == '_main_':
    app.run(host='localhost', port=5000, debug=True)
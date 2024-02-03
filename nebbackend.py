from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, MetaData
from flask_cors import CORS
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nebula.db'
db = SQLAlchemy(app)
CORS(app)

# Define models based on the provided schema
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    attendance_average = db.Column(db.Float, nullable=False)
    assignment_completion = db.Column(db.Integer, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    cohort = db.Column(db.String(255), nullable=False)

class WeeklyAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    week = db.Column(db.String(255), nullable=False)
    present = db.Column(db.Integer, nullable=False)
    absent = db.Column(db.Integer, nullable=False)

    _table_args_ = (
        db.UniqueConstraint('student_id', 'week', name='unique_student_week'),
    )

# Create database tables and insert data if they don't exist
@app.before_request
def setup_database():
    existing_tables = MetaData().reflect(bind=db.engine)
    if not existing_tables:
        db.create_all()

        # Insert data into the database if tables are newly created
        students_data = [
            {'name': 'John Doe', 'email': 'johndoe@example.com', 'attendance_average': 90.00, 'assignment_completion': 10, 'ranking': 5, 'cohort': 'Cohort 1'},
            {'name': 'Jane Smith', 'email': 'janesmith@example.com', 'attendance_average': 80.00, 'assignment_completion': 5, 'ranking': 10, 'cohort': 'Cohort 2'},
            {'name': 'Mike Tyson', 'email': 'miketyson@email.com', 'attendance_average': 30.00, 'assignment_completion': 12, 'ranking': 15, 'cohort': 'Cohort 2'},
            {'name': 'John Cena', 'email': 'johncena@email.com', 'attendance_average': 20.00, 'assignment_completion': 20, 'ranking': 20, 'cohort': 'Cohort 2'}
        ]

        for student_data in students_data:
            # Check if email already exists in the database
            existing_student = Student.query.filter_by(email=student_data['email']).first()
            if existing_student:
                continue  # Skip insertion if email already exists
            student = Student(**student_data)
            db.session.add(student)

        attendance_data = [
            {'student_id': 1, 'week': 'Week 1', 'present': 4, 'absent': 1},
            {'student_id': 1, 'week': 'Week 2', 'present': 5, 'absent': 0},
            {'student_id': 1, 'week': 'Week 3', 'present': 4, 'absent': 1},
            {'student_id': 2, 'week': 'Week 1', 'present': 3, 'absent': 2},
            {'student_id': 2, 'week': 'Week 2', 'present': 2, 'absent': 3},
            {'student_id': 2, 'week': 'Week 3', 'present': 4, 'absent': 1},
            {'student_id': 3, 'week': 'Week 1', 'present': 2, 'absent': 3},
            {'student_id': 3, 'week': 'Week 2', 'present': 0, 'absent': 5},
            {'student_id': 3, 'week': 'Week 3', 'present': 1, 'absent': 4},
            {'student_id': 4, 'week': 'Week 1', 'present': 5, 'absent': 0},
            {'student_id': 4, 'week': 'Week 2', 'present': 5, 'absent': 0},
            {'student_id': 4, 'week': 'Week 3', 'present': 3, 'absent': 2},
        ]

        for attendance_item in attendance_data:
            # Check if the entry already exists in the database
            existing_attendance = WeeklyAttendance.query.filter_by(student_id=attendance_item['student_id'], week=attendance_item['week']).first()
            if existing_attendance:
                continue  # Skip insertion if the entry already exists
            attendance = WeeklyAttendance(**attendance_item)
            db.session.add(attendance)

        db.session.commit()

# Health check endpoint
@app.route('/api/health-check', methods=['GET'])
def health_check():
    return 'Service is healthy', 200

# API endpoint to get all students
@app.route('/api/students', methods=['GET'])
def get_all_students():
    students = Student.query.all()
    student_list = []
    for student in students:
        attendance_data = WeeklyAttendance.query.filter_by(student_id=student.id).all()
        student_data = {
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'attendance_average': float(student.attendance_average),
            'assignment_completion': student.assignment_completion,
            'ranking': student.ranking,
            'cohort': student.cohort,
            'weeklyAttendance': [{'week': data.week, 'present': data.present, 'absent': data.absent} for data in attendance_data]
        }
        student_list.append(student_data)
    return jsonify(student_list)

# Route to get a student's details by email
@app.route('/api/student/<email>', methods=['POST'])
def get_student_details(email):
    if request.method == 'POST':
        student = Student.query.filter_by(email=email).first()
        if student:
            attendance_data = WeeklyAttendance.query.filter_by(student_id=student.id).all()
            student_data = {
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'attendance_average': float(student.attendance_average),
                'assignment_completion': student.assignment_completion,
                'ranking': student.ranking,
                'cohort': student.cohort,
                'weeklyAttendance': [{'week': data.week, 'present': data.present, 'absent': data.absent} for data in attendance_data]
            }
            return jsonify(student=student_data)
        else:
            return jsonify({'message': 'Student not found'}), 404
    else:
        return jsonify({'message': 'Method not allowed'}), 405

# Route to get cohort statistics by cohort name
@app.route('/api/cohort/stats/<cohort_name>', methods=['GET'])
def get_cohort_stats(cohort_name):
    students_in_cohort = Student.query.filter_by(cohort=cohort_name).all()
    if students_in_cohort:
        total_students = len(students_in_cohort)
        total_attendance = sum(student.attendance_average for student in students_in_cohort)
        total_assignment_completion = sum(student.assignment_completion for student in students_in_cohort)
        average_attendance = total_attendance / total_students
        average_assignment_completion = total_assignment_completion / total_students
        cohort_stats = {
            'cohort_name': cohort_name,
            'total_students': total_students,
            'attendance_average': round(average_attendance, 2),
            'assignment_completion': round(average_assignment_completion, 2),
            'top_performer': max(students_in_cohort, key=lambda student: student.attendance_average).name,
            'top_performer_attendance': max(student.attendance_average for student in students_in_cohort)
        }
        return jsonify(cohort_stats)
    else:
        return 'Cohort not found', 404

# Route to get cohort attendance statistics by cohort name
@app.route('/api/cohort/attendance/<cohort_name>', methods=['GET'])
def get_cohort_attendance(cohort_name):
    attendance_data = db.session.query(WeeklyAttendance.week, func.sum(WeeklyAttendance.present).label('present'), func.sum(WeeklyAttendance.absent).label('absent')) \
                                .join(Student, Student.id == WeeklyAttendance.student_id) \
                                .filter(Student.cohort == cohort_name) \
                                .group_by(WeeklyAttendance.week) \
                                .all()
    if attendance_data:
        cohort_attendance = [{'week': week, 'attendanceAverage': (present / (present + absent)) * 100} for week, present, absent in attendance_data]
        return jsonify(cohort_attendance)
    else:
        return jsonify([])

# Route for testing the database connection
@app.route('/api/test-db-connection', methods=['GET', 'POST'])
def test_db_connection():
    if request.method == 'GET':
        try:
            result = db.session.execute(text('SELECT 1'))
            return 'Database connection is working', 200
        except Exception as e:
            return f'Database connection error: {str(e)}'
    elif request.method == 'POST':
        return 'Database connection is working and Received a POST request', 200
    else:
        return 'Method not allowed'

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)

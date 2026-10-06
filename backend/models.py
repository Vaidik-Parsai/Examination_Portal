import os
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

db = SQLAlchemy()

# Association table for User-Role many-to-many relationship
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('roles.id'))
)

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean(), default=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    # Relationships
    examiner_profile = db.relationship('ExaminerProfile', backref='user', uselist=False)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)
    admin_profile = db.relationship('AdminProfile', backref='user', uselist=False)

class AdminProfile(db.Model):
    __tablename__ = 'admin_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

class ExaminerProfile(db.Model):
    __tablename__ = 'examiner_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    contact = db.Column(db.String(120))
    department = db.Column(db.String(120))
    status = db.Column(db.String(20), default='active')
    slots = db.relationship('ExamSlot', backref='examiner', lazy=True)

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    bookings = db.relationship('Booking', backref='student', lazy=True)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    examinations = db.relationship('Examination', backref='course', lazy=True)

class Examination(db.Model):
    __tablename__ = 'examinations'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    exam_type = db.Column(db.String(50))
    duration = db.Column(db.Integer)  # minutes
    max_marks = db.Column(db.Integer)
    slot_creation_start = db.Column(db.DateTime)
    slot_creation_end = db.Column(db.DateTime)
    booking_start = db.Column(db.DateTime)
    booking_end = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')
    rubrics = db.relationship('Rubric', backref='examination', lazy=True)
    slots = db.relationship('ExamSlot', backref='examination', lazy=True)

class Rubric(db.Model):
    __tablename__ = 'rubrics'
    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    criterion_name = db.Column(db.String(120), nullable=False)
    max_marks = db.Column(db.Integer)
    weightage = db.Column(db.Float)
    description = db.Column(db.Text)

class ExamSlot(db.Model):
    __tablename__ = 'exam_slots'
    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner_profiles.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='available')
    meeting_link = db.Column(db.String(255))
    bookings = db.relationship('Booking', backref='slot', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('exam_slots.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='booked')
    evaluation = db.relationship('Evaluation', backref='booking', uselist=False)

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner_profiles.id'), nullable=False)
    total_marks = db.Column(db.Integer)
    remarks = db.Column(db.Text)
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')

def init_roles_and_admin(user_datastore):
    """Programmatically seed roles and the default admin."""
    from flask_security.utils import hash_password
    
    for role in ['admin', 'examiner', 'student']:
        if not user_datastore.find_role(role):
            user_datastore.create_role(name=role, description=f"{role.capitalize()} Role")
    db.session.commit()

    admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    if not user_datastore.find_user(email=admin_email):
        admin_user = user_datastore.create_user(
            email=admin_email, 
            password=hash_password(os.getenv('ADMIN_PASSWORD', 'admin123')),
            name="Admin",
            roles=['admin'],
            fs_uniquifier=uuid.uuid4().hex
        )
        db.session.commit()
        admin_profile = AdminProfile(user_id=admin_user.id)
        db.session.add(admin_profile)
        db.session.commit()
        print('Default admin created.')

"""
Admin Routes — all endpoints protected by @roles_required('admin').
Handles: Dashboard, Courses, Exams, Rubrics, Examiner creation.
"""
import uuid
from datetime import datetime
from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_security import auth_required, roles_required
from flask_security.utils import hash_password

from models import (
    db, Course, Examination, Rubric, ExamSlot,
    ExaminerProfile, StudentProfile, Booking
)

# Create Blueprint and Api
admin_bp = Blueprint('admin', __name__)
admin_api = Api(admin_bp)

# --- Admin Dashboard ---
class AdminDashboardResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Returns summary stats for the admin dashboard."""
        stats = {
            "total_courses": Course.query.count(),
            "total_exams": Examination.query.count(),
            "total_examiners": ExaminerProfile.query.count(),
            "total_students": StudentProfile.query.count(),
            "total_bookings": Booking.query.count(),
            "pending_evaluations": Booking.query.filter_by(status='booked').count(),
        }
        return {"message": "Admin Dashboard", "stats": stats}

# --- Course CRUD ---
class CourseListResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """List all courses."""
        courses = Course.query.all()
        result = []
        for c in courses:
            result.append({
                "id": c.id, "code": c.code, "name": c.name,
                "description": c.description, "status": c.status
            })
        return {"courses": result}

    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Create a new course."""
        data = request.get_json()
        code = data.get('code')
        name = data.get('name')

        if not code or not name:
            return {"message": "Course code and name are required"}, 400

        if Course.query.filter_by(code=code).first():
            return {"message": f"Course with code '{code}' already exists"}, 400

        course = Course(
            code=code, name=name,
            description=data.get('description', ''),
            status=data.get('status', 'active')
        )
        db.session.add(course)
        db.session.commit()
        return {"message": "Course created", "id": course.id}, 201

class CourseResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, course_id):
        """Get a single course by ID."""
        course = Course.query.get_or_404(course_id)
        return {
            "id": course.id, "code": course.code, "name": course.name,
            "description": course.description, "status": course.status
        }

    @auth_required('token')
    @roles_required('admin')
    def put(self, course_id):
        """Update a course."""
        course = Course.query.get_or_404(course_id)
        data = request.get_json()
        course.name = data.get('name', course.name)
        course.description = data.get('description', course.description)
        course.status = data.get('status', course.status)
        db.session.commit()
        return {"message": "Course updated"}

    @auth_required('token')
    @roles_required('admin')
    def delete(self, course_id):
        """Delete a course."""
        course = Course.query.get_or_404(course_id)
        db.session.delete(course)
        db.session.commit()
        return {"message": "Course deleted"}

# --- Examination CRUD ---
class ExamListResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """List all examinations."""
        exams = Examination.query.all()
        result = []
        for e in exams:
            result.append({
                "id": e.id, "course_id": e.course_id,
                "course_name": e.course.name,
                "name": e.name, "exam_type": e.exam_type,
                "duration": e.duration, "max_marks": e.max_marks,
                "slot_creation_start": str(e.slot_creation_start) if e.slot_creation_start else None,
                "slot_creation_end": str(e.slot_creation_end) if e.slot_creation_end else None,
                "booking_start": str(e.booking_start) if e.booking_start else None,
                "booking_end": str(e.booking_end) if e.booking_end else None,
                "status": e.status
            })
        return {"exams": result}

    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Create a new examination."""
        data = request.get_json()
        course_id = data.get('course_id')
        name = data.get('name')

        if not course_id or not name:
            return {"message": "course_id and name are required"}, 400

        course = Course.query.get(course_id)
        if not course:
            return {"message": "Course not found"}, 404

        exam = Examination(
            course_id=course_id,
            name=name,
            exam_type=data.get('exam_type', 'written'),
            duration=data.get('duration'),
            max_marks=data.get('max_marks'),
            slot_creation_start=datetime.fromisoformat(data['slot_creation_start']) if data.get('slot_creation_start') else None,
            slot_creation_end=datetime.fromisoformat(data['slot_creation_end']) if data.get('slot_creation_end') else None,
            booking_start=datetime.fromisoformat(data['booking_start']) if data.get('booking_start') else None,
            booking_end=datetime.fromisoformat(data['booking_end']) if data.get('booking_end') else None,
            status=data.get('status', 'draft')
        )
        db.session.add(exam)
        db.session.commit()
        return {"message": "Examination created", "id": exam.id}, 201

class ExamResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, exam_id):
        """Get a single examination."""
        e = Examination.query.get_or_404(exam_id)
        return {
            "id": e.id, "course_id": e.course_id,
            "course_name": e.course.name,
            "name": e.name, "exam_type": e.exam_type,
            "duration": e.duration, "max_marks": e.max_marks,
            "slot_creation_start": str(e.slot_creation_start) if e.slot_creation_start else None,
            "slot_creation_end": str(e.slot_creation_end) if e.slot_creation_end else None,
            "booking_start": str(e.booking_start) if e.booking_start else None,
            "booking_end": str(e.booking_end) if e.booking_end else None,
            "status": e.status
        }

    @auth_required('token')
    @roles_required('admin')
    def put(self, exam_id):
        """Update an examination."""
        e = Examination.query.get_or_404(exam_id)
        data = request.get_json()
        e.name = data.get('name', e.name)
        e.exam_type = data.get('exam_type', e.exam_type)
        e.duration = data.get('duration', e.duration)
        e.max_marks = data.get('max_marks', e.max_marks)
        e.status = data.get('status', e.status)
        if data.get('slot_creation_start'):
            e.slot_creation_start = datetime.fromisoformat(data['slot_creation_start'])
        if data.get('slot_creation_end'):
            e.slot_creation_end = datetime.fromisoformat(data['slot_creation_end'])
        if data.get('booking_start'):
            e.booking_start = datetime.fromisoformat(data['booking_start'])
        if data.get('booking_end'):
            e.booking_end = datetime.fromisoformat(data['booking_end'])
        db.session.commit()
        return {"message": "Examination updated"}

    @auth_required('token')
    @roles_required('admin')
    def delete(self, exam_id):
        """Delete an examination."""
        e = Examination.query.get_or_404(exam_id)
        db.session.delete(e)
        db.session.commit()
        return {"message": "Examination deleted"}

# --- Rubric CRUD ---
class RubricListResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, exam_id):
        """List all rubrics for a specific exam."""
        rubrics = Rubric.query.filter_by(examination_id=exam_id).all()
        result = []
        for r in rubrics:
            result.append({
                "id": r.id, "criterion_name": r.criterion_name,
                "max_marks": r.max_marks, "weightage": r.weightage,
                "description": r.description
            })
        return {"rubrics": result}

    @auth_required('token')
    @roles_required('admin')
    def post(self, exam_id):
        """Add a rubric to an exam."""
        exam = Examination.query.get(exam_id)
        if not exam:
            return {"message": "Examination not found"}, 404

        data = request.get_json()
        if not data.get('criterion_name'):
            return {"message": "criterion_name is required"}, 400

        rubric = Rubric(
            examination_id=exam_id,
            criterion_name=data['criterion_name'],
            max_marks=data.get('max_marks'),
            weightage=data.get('weightage'),
            description=data.get('description', '')
        )
        db.session.add(rubric)
        db.session.commit()
        return {"message": "Rubric created", "id": rubric.id}, 201

class RubricResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def put(self, rubric_id):
        """Update a rubric."""
        r = Rubric.query.get_or_404(rubric_id)
        data = request.get_json()
        r.criterion_name = data.get('criterion_name', r.criterion_name)
        r.max_marks = data.get('max_marks', r.max_marks)
        r.weightage = data.get('weightage', r.weightage)
        r.description = data.get('description', r.description)
        db.session.commit()
        return {"message": "Rubric updated"}

    @auth_required('token')
    @roles_required('admin')
    def delete(self, rubric_id):
        """Delete a rubric."""
        r = Rubric.query.get_or_404(rubric_id)
        db.session.delete(r)
        db.session.commit()
        return {"message": "Rubric deleted"}

# --- Examiner Management ---
class ExaminerListResource(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """List all examiners."""
        examiners = ExaminerProfile.query.all()
        result = []
        for ep in examiners:
            result.append({
                "id": ep.id, "user_id": ep.user_id,
                "name": ep.user.name, "email": ep.user.email,
                "contact": ep.contact, "department": ep.department,
                "status": ep.status
            })
        return {"examiners": result}

    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Admin creates a new examiner account."""
        from app import user_datastore  # lazy import to avoid circular dependency

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password or not name:
            return {"message": "email, password, and name are required"}, 400

        if user_datastore.find_user(email=email):
            return {"message": "Email already registered"}, 400

        user = user_datastore.create_user(
            email=email,
            password=hash_password(password),
            name=name,
            roles=['examiner'],
            fs_uniquifier=uuid.uuid4().hex
        )
        db.session.commit()

        examiner_profile = ExaminerProfile(
            user_id=user.id,
            contact=data.get('contact', ''),
            department=data.get('department', '')
        )
        db.session.add(examiner_profile)
        db.session.commit()

        return {"message": "Examiner created", "id": examiner_profile.id}, 201

# ==========================================
# REGISTER ALL ADMIN RESOURCES
# ==========================================
admin_api.add_resource(AdminDashboardResource, '/api/admin/dashboard')
admin_api.add_resource(CourseListResource, '/api/admin/courses')
admin_api.add_resource(CourseResource, '/api/admin/courses/<int:course_id>')
admin_api.add_resource(ExamListResource, '/api/admin/exams')
admin_api.add_resource(ExamResource, '/api/admin/exams/<int:exam_id>')
admin_api.add_resource(RubricListResource, '/api/admin/exams/<int:exam_id>/rubrics')
admin_api.add_resource(RubricResource, '/api/admin/rubrics/<int:rubric_id>')
admin_api.add_resource(ExaminerListResource, '/api/admin/examiners')

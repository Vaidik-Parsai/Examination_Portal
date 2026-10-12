"""
Student Routes — Phase 5 implementation.
Provides:
- GET /api/student/dashboard : student statistics
- GET /api/student/slots : list open exam slots available for booking
- POST /api/student/slots : book an available slot
- GET /api/student/bookings : list current student's bookings
- GET /api/student/evaluations : list current student's evaluations
All endpoints protected by @roles_required('student') and @auth_required('token').
"""
from datetime import datetime
from flask import Blueprint, request, abort
from flask_restful import Api, Resource
from flask_security import auth_required, roles_required, current_user

from models import db, ExamSlot, Booking, Evaluation, StudentProfile

# Blueprint & API setup
student_bp = Blueprint('student', __name__, url_prefix='/api/student')
student_api = Api(student_bp)


def _get_student_profile():
    """Retrieve the logged-in user's student profile or abort 403."""
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        abort(403, "Current user does not have a student profile.")
    return profile


class StudentDashboardResource(Resource):
    """GET = Summary metrics for the logged-in student."""

    @auth_required('token')
    @roles_required('student')
    def get(self):
        profile = _get_student_profile()
        total_bookings = Booking.query.filter_by(student_id=profile.id).count()
        upcoming_exams = Booking.query.filter_by(student_id=profile.id, status='booked').count()
        completed_exams = Booking.query.filter_by(student_id=profile.id, status='completed').count()

        return {
            "message": "Student Dashboard",
            "stats": {
                "total_bookings": total_bookings,
                "upcoming_exams": upcoming_exams,
                "completed_exams": completed_exams
            }
        }


class StudentSlotListResource(Resource):
    """GET = List all available examination slots open for booking.
       POST = Book an open slot."""

    @auth_required('token')
    @roles_required('student')
    def get(self):
        slots = ExamSlot.query.filter_by(status='available').filter(ExamSlot.available_seats > 0).all()
        now = datetime.utcnow()
        current_date = now.date()

        result = []
        for s in slots:
            if s.date < current_date:
                continue

            exam = s.examination
            if exam:
                if exam.booking_start and now < exam.booking_start:
                    continue
                if exam.booking_end and now > exam.booking_end:
                    continue

            result.append({
                'id': s.id,
                'examination_id': s.examination_id,
                'exam_name': exam.name if exam else None,
                'course_name': exam.course.name if exam and exam.course else None,
                'examiner_name': s.examiner.user.name if s.examiner and s.examiner.user else None,
                'date': s.date.isoformat(),
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat(),
                'available_seats': s.available_seats,
                'max_capacity': s.max_capacity,
                'meeting_link': s.meeting_link
            })

        return {"slots": result}

    @auth_required('token')
    @roles_required('student')
    def post(self):
        profile = _get_student_profile()
        data = request.get_json(force=True)
        slot_id = data.get('slot_id')

        if not slot_id:
            abort(400, "'slot_id' is required.")

        slot = ExamSlot.query.get_or_404(slot_id)

        if slot.status != 'available':
            abort(400, "This slot is no longer available.")
        if slot.available_seats <= 0:
            abort(400, "No seats available for this slot.")

        exam = slot.examination
        now = datetime.utcnow()
        if exam:
            if exam.booking_start and now < exam.booking_start:
                abort(400, "Booking for this examination has not opened yet.")
            if exam.booking_end and now > exam.booking_end:
                abort(400, "Booking deadline for this examination has passed.")

        existing = Booking.query.filter_by(slot_id=slot.id, student_id=profile.id).first()
        if existing:
            abort(400, "You have already booked this slot.")

        booking = Booking(
            slot_id=slot.id,
            student_id=profile.id,
            status='booked',
            booking_date=now
        )
        slot.available_seats -= 1
        db.session.add(booking)
        db.session.commit()

        return {
            "message": "Slot booked successfully",
            "booking": {
                'id': booking.id,
                'slot_id': booking.slot_id,
                'student_id': booking.student_id,
                'status': booking.status,
                'booking_date': booking.booking_date.isoformat()
            }
        }, 201


class StudentBookingListResource(Resource):
    """GET = List all bookings for the logged-in student."""

    @auth_required('token')
    @roles_required('student')
    def get(self):
        profile = _get_student_profile()
        bookings = Booking.query.filter_by(student_id=profile.id).all()

        result = []
        for b in bookings:
            slot = b.slot
            exam = slot.examination if slot else None
            result.append({
                'id': b.id,
                'slot_id': b.slot_id,
                'status': b.status,
                'booking_date': b.booking_date.isoformat() if b.booking_date else None,
                'exam_name': exam.name if exam else None,
                'course_name': exam.course.name if exam and exam.course else None,
                'date': slot.date.isoformat() if slot and slot.date else None,
                'start_time': slot.start_time.isoformat() if slot and slot.start_time else None,
                'end_time': slot.end_time.isoformat() if slot and slot.end_time else None,
                'meeting_link': slot.meeting_link if slot else None
            })

        return {"bookings": result}


class StudentEvaluationListResource(Resource):
    """GET = List all evaluations for the logged-in student."""

    @auth_required('token')
    @roles_required('student')
    def get(self):
        profile = _get_student_profile()
        evaluations = Evaluation.query.join(Booking).filter(Booking.student_id == profile.id).all()

        result = []
        for e in evaluations:
            booking = e.booking
            slot = booking.slot if booking else None
            exam = slot.examination if slot else None
            result.append({
                'id': e.id,
                'booking_id': e.booking_id,
                'exam_name': exam.name if exam else None,
                'examiner_name': e.examiner.user.name if e.examiner and e.examiner.user else None,
                'total_marks': e.total_marks,
                'remarks': e.remarks,
                'status': e.status,
                'evaluation_date': e.evaluation_date.isoformat() if e.evaluation_date else None
            })

        return {"evaluations": result}


# Register student resources
student_api.add_resource(StudentDashboardResource, '/dashboard')
student_api.add_resource(StudentSlotListResource, '/slots')
student_api.add_resource(StudentBookingListResource, '/bookings')
student_api.add_resource(StudentEvaluationListResource, '/evaluations')

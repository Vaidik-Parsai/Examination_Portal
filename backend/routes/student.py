"""
Student endpoints: available slot booking, booking history, profile, and exam evaluations.
"""
from datetime import datetime
from flask import Blueprint, request, abort
from flask_restful import Api, Resource
from flask_security import auth_required, roles_required, current_user
from flask_security.utils import hash_password

from models import db, ExamSlot, Booking, Evaluation, StudentProfile, ExaminerProfile, User

# Blueprint & API setup
student_bp = Blueprint('student', __name__, url_prefix='/api/student')
student_api = Api(student_bp)

# Cancellation deadline: students can cancel up to this many hours before the slot
CANCEL_DEADLINE_HOURS = 24


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


class StudentProfileResource(Resource):
    """GET = View own profile details. PUT = Update own profile."""

    @auth_required('token')
    @roles_required('student')
    def get(self):
        profile = _get_student_profile()
        user = current_user
        return {
            "id": profile.id,
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "active": user.active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "total_bookings": len(profile.bookings)
        }

    @auth_required('token')
    @roles_required('student')
    def put(self):
        profile = _get_student_profile()
        user = current_user
        data = request.get_json(force=True)

        new_name = data.get('name', '').strip()
        new_password = data.get('password', '').strip()

        if not new_name:
            return {"message": "Name cannot be empty."}, 400
        if len(new_name) < 2:
            return {"message": "Name must be at least 2 characters."}, 400

        user.name = new_name

        if new_password:
            if len(new_password) < 6:
                return {"message": "Password must be at least 6 characters."}, 400
            user.password = hash_password(new_password)

        db.session.commit()
        return {"message": "Profile updated successfully.", "name": user.name}


class StudentSlotListResource(Resource):
    """GET = List all available examination slots open for booking.
       POST = Book an open slot."""

    @auth_required('token')
    @roles_required('student')
    def get(self):
        # Filter params for examiner search
        examiner_q = request.args.get('examiner', '').strip().lower()
        subject_q = request.args.get('subject', '').strip().lower()

        slots = ExamSlot.query.filter_by(status='available').filter(ExamSlot.available_seats > 0).all()
        now = datetime.utcnow()
        current_date = now.date()

        result = []
        for s in slots:
            if s.date < current_date:
                continue

            exam = s.examination
            if exam:
                if exam.status == 'closed':
                    continue
                if exam.booking_start and now < exam.booking_start:
                    continue
                if exam.booking_end and now > exam.booking_end:
                    continue

            examiner_name = s.examiner.user.name if s.examiner and s.examiner.user else ''
            course_name = exam.course.name if exam and exam.course else ''
            exam_name = exam.name if exam else ''

            # Apply search filters
            if examiner_q and examiner_q not in examiner_name.lower():
                continue
            if subject_q and subject_q not in course_name.lower() and subject_q not in exam_name.lower():
                continue

            result.append({
                'id': s.id,
                'examination_id': s.examination_id,
                'exam_name': exam_name or None,
                'course_name': course_name or None,
                'examiner_name': examiner_name or None,
                'examiner_department': s.examiner.department if s.examiner else None,
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
            abort(400, "This slot is no longer available for booking.")
        if slot.available_seats <= 0:
            abort(400, "No seats available for this slot.")

        exam = slot.examination
        now = datetime.utcnow()
        if exam:
            if exam.status == 'closed':
                abort(400, "Booking for this examination is currently closed by the administrator.")
            if exam.booking_start and now < exam.booking_start:
                abort(400, "Booking for this examination has not opened yet.")
            if exam.booking_end and now > exam.booking_end:
                abort(400, "Booking deadline for this examination has passed.")

        existing = Booking.query.filter_by(slot_id=slot.id, student_id=profile.id).first()
        if existing and existing.status != 'cancelled':
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
        now = datetime.utcnow()

        result = []
        for b in bookings:
            slot = b.slot
            exam = slot.examination if slot else None

            # Compute cancellation eligibility
            can_cancel = False
            deadline_msg = None
            if b.status == 'booked' and slot and slot.date:
                from datetime import timedelta
                slot_dt = datetime.combine(slot.date, slot.start_time)
                hours_left = (slot_dt - now).total_seconds() / 3600
                if hours_left >= CANCEL_DEADLINE_HOURS:
                    can_cancel = True
                else:
                    deadline_msg = f"Cancellation closed — less than {CANCEL_DEADLINE_HOURS}h before exam."

            result.append({
                'id': b.id,
                'slot_id': b.slot_id,
                'status': b.status,
                'booking_date': b.booking_date.isoformat() if b.booking_date else None,
                'reschedule_notice': getattr(b, 'reschedule_notice', None),
                'exam_name': exam.name if exam else None,
                'course_name': exam.course.name if exam and exam.course else None,
                'date': slot.date.isoformat() if slot and slot.date else None,
                'start_time': slot.start_time.isoformat() if slot and slot.start_time else None,
                'end_time': slot.end_time.isoformat() if slot and slot.end_time else None,
                'meeting_link': slot.meeting_link if slot else None,
                'can_cancel': can_cancel,
                'cancel_deadline_msg': deadline_msg
            })

        return {"bookings": result}


class StudentBookingCancelResource(Resource):
    """DELETE = Cancel a booking before the cancellation deadline."""

    @auth_required('token')
    @roles_required('student')
    def delete(self, booking_id):
        profile = _get_student_profile()
        booking = Booking.query.get_or_404(booking_id)

        if booking.student_id != profile.id:
            abort(403, "You do not own this booking.")

        if booking.status == 'cancelled':
            return {"message": "This booking is already cancelled."}, 400

        if booking.status == 'completed':
            return {"message": "Cannot cancel a completed booking."}, 400

        # Enforce deadline
        slot = booking.slot
        now = datetime.utcnow()
        if slot and slot.date:
            from datetime import timedelta
            slot_dt = datetime.combine(slot.date, slot.start_time)
            hours_left = (slot_dt - now).total_seconds() / 3600
            if hours_left < CANCEL_DEADLINE_HOURS:
                return {
                    "message": f"Cancellation deadline passed. You can only cancel more than {CANCEL_DEADLINE_HOURS} hours before the exam."
                }, 400

        # Replenish the seat
        if slot:
            slot.available_seats += 1
            if slot.status == 'full':
                slot.status = 'available'

        booking.status = 'cancelled'
        db.session.commit()

        return {"message": "Booking cancelled successfully. The seat has been released."}


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
            examiner = slot.examiner if slot else None
            examiner_user = examiner.user if examiner and examiner.user else None
            result.append({
                'id': e.id,
                'booking_id': e.booking_id,
                'exam_name': exam.name if exam else None,
                'course_name': exam.course.name if exam and exam.course else None,
                'examiner_name': examiner_user.name if examiner_user else None,
                'total_marks': e.total_marks,
                'max_marks': exam.max_marks if exam else None,
                'remarks': e.remarks,
                'status': e.status,
                'evaluation_date': e.evaluation_date.isoformat() if e.evaluation_date else None
            })

        return {"evaluations": result}


# Register student resources
student_api.add_resource(StudentDashboardResource, '/dashboard')
student_api.add_resource(StudentProfileResource, '/profile')
student_api.add_resource(StudentSlotListResource, '/slots')
student_api.add_resource(StudentBookingListResource, '/bookings')
student_api.add_resource(StudentBookingCancelResource, '/bookings/<int:booking_id>/cancel')
student_api.add_resource(StudentEvaluationListResource, '/evaluations')

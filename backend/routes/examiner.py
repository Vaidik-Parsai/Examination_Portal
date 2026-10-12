"""
Examiner Routes — Phase 4 implementation.
Provides slot CRUD, bookings view, evaluation submission, slot completion, and examiner dashboard.
All endpoints protected by @roles_required('examiner') and @auth_required('token').
"""
from datetime import datetime
from flask import Blueprint, request, abort
from flask_restful import Resource, Api
from flask_security import auth_required, roles_required, current_user

from models import db, ExamSlot, Booking, Evaluation, Examination, Rubric, ExaminerProfile

# Blueprint & API setup
examiner_bp = Blueprint('examiner', __name__, url_prefix='/api/examiner')
examiner_api = Api(examiner_bp)


def _get_examiner_profile():
    """Retrieve the logged-in user's examiner profile or abort 403."""
    profile = ExaminerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        abort(403, "Current user does not have an examiner profile.")
    return profile


def _examiner_slot_or_404(slot_id, examiner_id):
    """Retrieve slot and verify examiner ownership."""
    slot = ExamSlot.query.get_or_404(slot_id)
    if slot.examiner_id != examiner_id:
        abort(403, "You do not own this slot.")
    return slot


class ExaminerDashboardResource(Resource):
    """GET = Summary metrics for the logged-in examiner."""

    @auth_required('token')
    @roles_required('examiner')
    def get(self):
        profile = _get_examiner_profile()
        total_slots = ExamSlot.query.filter_by(examiner_id=profile.id).count()
        active_slots = ExamSlot.query.filter_by(examiner_id=profile.id, status='available').count()
        total_evaluations = Evaluation.query.filter_by(examiner_id=profile.id).count()
        pending_evaluations = Booking.query.join(ExamSlot).filter(
            ExamSlot.examiner_id == profile.id,
            Booking.status == 'booked'
        ).count()

        return {
            "message": "Examiner Dashboard",
            "stats": {
                "total_slots": total_slots,
                "active_slots": active_slots,
                "total_evaluations": total_evaluations,
                "pending_evaluations": pending_evaluations
            }
        }


class ExaminerSlotListResource(Resource):
    """GET = List all slots for the logged-in examiner.
       POST = Create a new slot for an examination within slot creation window."""

    @auth_required('token')
    @roles_required('examiner')
    def get(self):
        profile = _get_examiner_profile()
        slots = ExamSlot.query.filter_by(examiner_id=profile.id).all()
        result = []
        for s in slots:
            result.append({
                'id': s.id,
                'examination_id': s.examination_id,
                'exam_name': s.examination.name if s.examination else None,
                'date': s.date.isoformat(),
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat(),
                'max_capacity': s.max_capacity,
                'available_seats': s.available_seats,
                'status': s.status,
                'meeting_link': s.meeting_link
            })
        return {"slots": result}

    @auth_required('token')
    @roles_required('examiner')
    def post(self):
        profile = _get_examiner_profile()
        data = request.get_json(force=True)

        exam_id = data.get('examination_id') or data.get('exam_id')
        date_str = data.get('date')
        start_str = data.get('start_time')
        end_str = data.get('end_time')
        max_capacity = data.get('max_capacity')

        if not all([exam_id, date_str, start_str, end_str, max_capacity]):
            abort(400, "examination_id, date, start_time, end_time, max_capacity are required.")

        exam = Examination.query.get_or_404(exam_id)
        now = datetime.utcnow()
        if exam.slot_creation_start and now < exam.slot_creation_start:
            abort(400, "Slot creation window has not opened yet.")
        if exam.slot_creation_end and now > exam.slot_creation_end:
            abort(400, "Slot creation window has closed.")

        try:
            slot_date = datetime.fromisoformat(date_str).date()
            start_time = datetime.fromisoformat(start_str).time()
            end_time = datetime.fromisoformat(end_str).time()
        except Exception:
            abort(400, "Invalid date or time format. Use ISO format (YYYY-MM-DD, HH:MM:SS).")

        slot = ExamSlot(
            examination_id=exam.id,
            examiner_id=profile.id,
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
            max_capacity=int(max_capacity),
            available_seats=int(max_capacity),
            status='available',
            meeting_link=data.get('meeting_link')
        )
        db.session.add(slot)
        db.session.commit()

        return {
            "message": "Slot created successfully",
            "id": slot.id
        }, 201


class ExaminerSlotResource(Resource):
    """PUT = Update a slot.
       DELETE = Delete a slot (if no bookings exist)."""

    @auth_required('token')
    @roles_required('examiner')
    def put(self, slot_id):
        profile = _get_examiner_profile()
        slot = _examiner_slot_or_404(slot_id, profile.id)
        data = request.get_json(force=True)

        if 'date' in data:
            try:
                slot.date = datetime.fromisoformat(data['date']).date()
            except Exception:
                abort(400, "Invalid date format.")
        if 'start_time' in data:
            try:
                slot.start_time = datetime.fromisoformat(data['start_time']).time()
            except Exception:
                abort(400, "Invalid start_time format.")
        if 'end_time' in data:
            try:
                slot.end_time = datetime.fromisoformat(data['end_time']).time()
            except Exception:
                abort(400, "Invalid end_time format.")
        if 'max_capacity' in data:
            new_capacity = int(data['max_capacity'])
            booked = slot.max_capacity - slot.available_seats
            if new_capacity < booked:
                abort(400, "New capacity cannot be less than already booked seats.")
            slot.max_capacity = new_capacity
            slot.available_seats = new_capacity - booked
        if 'meeting_link' in data:
            slot.meeting_link = data['meeting_link']
        if 'status' in data:
            slot.status = data['status']

        db.session.commit()
        return {"message": "Slot updated"}

    @auth_required('token')
    @roles_required('examiner')
    def delete(self, slot_id):
        profile = _get_examiner_profile()
        slot = _examiner_slot_or_404(slot_id, profile.id)
        if slot.bookings:
            abort(400, "Cannot delete a slot with existing bookings.")
        db.session.delete(slot)
        db.session.commit()
        return {"message": "Slot deleted"}


class ExaminerSlotBookingsResource(Resource):
    """GET = List all student bookings for an examiner's slot."""

    @auth_required('token')
    @roles_required('examiner')
    def get(self, slot_id):
        profile = _get_examiner_profile()
        slot = _examiner_slot_or_404(slot_id, profile.id)

        bookings_data = []
        for b in slot.bookings:
            student_user = b.student.user if b.student and b.student.user else None
            bookings_data.append({
                "booking_id": b.id,
                "student_id": b.student_id,
                "student_name": student_user.name if student_user else "Unknown",
                "student_email": student_user.email if student_user else None,
                "booking_date": b.booking_date.isoformat() if b.booking_date else None,
                "status": b.status,
                "evaluation": {
                    "id": b.evaluation.id,
                    "total_marks": b.evaluation.total_marks,
                    "remarks": b.evaluation.remarks,
                    "status": b.evaluation.status
                } if b.evaluation else None
            })

        return {"bookings": bookings_data}


class EvaluationSubmitResource(Resource):
    """POST = Submit or update an evaluation for a booking."""

    @auth_required('token')
    @roles_required('examiner')
    def post(self):
        profile = _get_examiner_profile()
        data = request.get_json(force=True)

        booking_id = data.get('booking_id')
        total_marks = data.get('total_marks')
        remarks = data.get('remarks', '')

        if booking_id is None or total_marks is None:
            abort(400, "booking_id and total_marks are required.")

        booking = Booking.query.get_or_404(booking_id)
        if booking.slot.examiner_id != profile.id:
            abort(403, "You do not own the slot for this booking.")

        evaluation = Evaluation.query.filter_by(booking_id=booking.id).first()
        if not evaluation:
            evaluation = Evaluation(
                booking_id=booking.id,
                examiner_id=profile.id,
                total_marks=total_marks,
                remarks=remarks,
                evaluation_date=datetime.utcnow(),
                status='completed'
            )
            db.session.add(evaluation)
        else:
            evaluation.total_marks = total_marks
            evaluation.remarks = remarks
            evaluation.evaluation_date = datetime.utcnow()
            evaluation.status = 'completed'

        booking.status = 'completed'
        db.session.commit()

        return {
            "message": "Evaluation submitted successfully",
            "evaluation": {
                "id": evaluation.id,
                "booking_id": evaluation.booking_id,
                "total_marks": evaluation.total_marks,
                "remarks": evaluation.remarks,
                "status": evaluation.status
            }
        }, 201


class SlotCompleteResource(Resource):
    """POST = Mark a slot as completed once all bookings have been evaluated."""

    @auth_required('token')
    @roles_required('examiner')
    def post(self, slot_id):
        profile = _get_examiner_profile()
        slot = _examiner_slot_or_404(slot_id, profile.id)

        unevaluated = [b.id for b in slot.bookings if not b.evaluation]
        if unevaluated:
            abort(400, f"Cannot complete slot. Unevaluated booking IDs: {unevaluated}")

        slot.status = 'completed'
        db.session.commit()
        return {"message": "Slot marked as completed"}


# Register all examiner resources
examiner_api.add_resource(ExaminerDashboardResource, '/dashboard')
examiner_api.add_resource(ExaminerSlotListResource, '/slots')
examiner_api.add_resource(ExaminerSlotResource, '/slots/<int:slot_id>')
examiner_api.add_resource(ExaminerSlotBookingsResource, '/slots/<int:slot_id>/bookings')
examiner_api.add_resource(EvaluationSubmitResource, '/evaluations')
examiner_api.add_resource(SlotCompleteResource, '/slots/<int:slot_id>/complete')

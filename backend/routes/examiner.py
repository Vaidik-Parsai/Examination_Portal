"""
Examiner endpoints: slot management, bookings inspection, and student evaluations.
"""
from datetime import datetime, date, time
from flask import Blueprint, request, abort
from flask_restful import Resource, Api
from flask_security import auth_required, roles_required, current_user

from models import db, ExamSlot, Booking, Evaluation, Examination, Rubric, ExaminerProfile

# Blueprint & API setup
examiner_bp = Blueprint('examiner', __name__, url_prefix='/api/examiner')
examiner_api = Api(examiner_bp)


def _parse_date(d_str):
    if not d_str:
        raise ValueError("Missing date")
    d_str = str(d_str).strip().split('T')[0]
    return date.fromisoformat(d_str)


def _parse_time(t_str):
    if not t_str:
        raise ValueError("Missing time")
    t_str = str(t_str).strip()
    parts = t_str.split(':')
    if len(parts) == 2:
        return time(int(parts[0]), int(parts[1]))
    elif len(parts) == 3:
        sec_parts = parts[2].split('.')
        return time(int(parts[0]), int(parts[1]), int(sec_parts[0]))
    return time.fromisoformat(t_str)


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


def check_examiner_overlap(examiner_id, slot_date, start_time, end_time, exclude_slot_id=None):
    """Detect if an examiner already has an overlapping slot scheduled on that date."""
    query = ExamSlot.query.filter(
        ExamSlot.examiner_id == examiner_id,
        ExamSlot.date == slot_date,
        ExamSlot.status != 'cancelled'
    )
    if exclude_slot_id:
        query = query.filter(ExamSlot.id != exclude_slot_id)

    for existing in query.all():
        if start_time < existing.end_time and end_time > existing.start_time:
            return existing
    return None


class ExaminerSlotListResource(Resource):
    """GET = List all slots for the logged-in examiner with rubric metadata.
       POST = Create a new slot for an examination within slot creation window."""

    @auth_required('token')
    @roles_required('examiner')
    def get(self):
        profile = _get_examiner_profile()
        slots = ExamSlot.query.filter_by(examiner_id=profile.id).all()
        result = []
        for s in slots:
            exam = s.examination
            rubrics_data = [
                {
                    'id': r.id,
                    'criterion_name': r.criterion_name,
                    'max_marks': r.max_marks,
                    'weightage': r.weightage,
                    'description': r.description
                }
                for r in (exam.rubrics if exam else [])
            ]
            booked_count = len([b for b in s.bookings if b.status != 'cancelled'])
            result.append({
                'id': s.id,
                'examination_id': s.examination_id,
                'exam_name': exam.name if exam else None,
                'course_name': exam.course.name if exam and exam.course else None,
                'date': s.date.isoformat(),
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat(),
                'max_capacity': s.max_capacity,
                'available_seats': s.available_seats,
                'booked_count': booked_count,
                'status': s.status,
                'meeting_link': s.meeting_link,
                'rubrics': rubrics_data
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
            slot_date = _parse_date(date_str)
            start_time = _parse_time(start_str)
            end_time = _parse_time(end_str)
        except Exception as e:
            abort(400, f"Invalid date or time format: {str(e)}. Use format (YYYY-MM-DD, HH:MM[:SS]).")

        if start_time >= end_time:
            abort(400, "start_time must be earlier than end_time.")

        # Prevent double-booking for the examiner
        conflict = check_examiner_overlap(profile.id, slot_date, start_time, end_time)
        if conflict:
            abort(400, f"Scheduling Conflict: You already have another slot scheduled on {slot_date} ({conflict.start_time.strftime('%H:%M')} – {conflict.end_time.strftime('%H:%M')}).")

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
    """PUT = Update a slot (allowed ONLY before student booking).
       DELETE = Delete a slot (if no bookings exist)."""

    @auth_required('token')
    @roles_required('examiner')
    def put(self, slot_id):
        profile = _get_examiner_profile()
        slot = _examiner_slot_or_404(slot_id, profile.id)

        # STRICT VALIDATION: Examiner can update a slot only BEFORE a student has booked it
        active_bookings = [b for b in slot.bookings if b.status != 'cancelled']
        if active_bookings:
            abort(400, "Cannot edit or reschedule this slot: a student has already booked it. Contact an administrator if adjustments are required.")

        data = request.get_json(force=True)

        target_date = slot.date
        target_start = slot.start_time
        target_end = slot.end_time

        if 'date' in data:
            try:
                target_date = _parse_date(data['date'])
            except Exception:
                abort(400, "Invalid date format.")
        if 'start_time' in data:
            try:
                target_start = _parse_time(data['start_time'])
            except Exception:
                abort(400, "Invalid start_time format.")
        if 'end_time' in data:
            try:
                target_end = _parse_time(data['end_time'])
            except Exception:
                abort(400, "Invalid end_time format.")

        if target_start >= target_end:
            abort(400, "start_time must be earlier than end_time.")

        # Prevent double-booking
        conflict = check_examiner_overlap(profile.id, target_date, target_start, target_end, exclude_slot_id=slot.id)
        if conflict:
            abort(400, f"Scheduling Conflict: You already have another slot scheduled on {target_date} ({conflict.start_time.strftime('%H:%M')} – {conflict.end_time.strftime('%H:%M')}).")

        slot.date = target_date
        slot.start_time = target_start
        slot.end_time = target_end

        if 'max_capacity' in data:
            new_capacity = int(data['max_capacity'])
            slot.max_capacity = new_capacity
            slot.available_seats = new_capacity
        if 'meeting_link' in data:
            slot.meeting_link = data['meeting_link']
        if 'status' in data:
            slot.status = data['status']

        db.session.commit()
        return {"message": "Slot updated successfully"}

    @auth_required('token')
    @roles_required('examiner')
    def delete(self, slot_id):
        profile = _get_examiner_profile()
        slot = _examiner_slot_or_404(slot_id, profile.id)
        active_bookings = [b for b in slot.bookings if b.status != 'cancelled']
        if active_bookings:
            abort(400, "Cannot delete a slot with existing student bookings.")
        db.session.delete(slot)
        db.session.commit()
        return {"message": "Slot deleted"}


class ExaminerSlotBookingsResource(Resource):
    """GET = List all student bookings for an examiner's slot with full rubrics metadata."""

    @auth_required('token')
    @roles_required('examiner')
    def get(self, slot_id):
        profile = _get_examiner_profile()
        slot = _examiner_slot_or_404(slot_id, profile.id)
        exam = slot.examination

        # Expose rubrics for this subject/exam to the examiner
        rubrics_data = [
            {
                "id": r.id,
                "criterion_name": r.criterion_name,
                "max_marks": r.max_marks,
                "weightage": r.weightage,
                "description": r.description
            }
            for r in (exam.rubrics if exam else [])
        ]

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
                "reschedule_notice": getattr(b, 'reschedule_notice', None),
                "evaluation": {
                    "id": b.evaluation.id,
                    "total_marks": b.evaluation.total_marks,
                    "remarks": b.evaluation.remarks,
                    "status": b.evaluation.status
                } if b.evaluation else None
            })

        return {
            "slot": {
                "id": slot.id,
                "examination_id": slot.examination_id,
                "exam_name": exam.name if exam else "Unknown Exam",
                "course_name": exam.course.name if exam and exam.course else "Unknown Course",
                "exam_type": exam.exam_type if exam else "",
                "duration": exam.duration if exam else 0,
                "max_marks": exam.max_marks if exam else 100,
                "date": slot.date.isoformat(),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "status": slot.status,
                "meeting_link": slot.meeting_link
            },
            "rubrics": rubrics_data,
            "bookings": bookings_data
        }


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


class ExaminerExamListResource(Resource):
    """GET = List all examinations available for scheduling slots with their rubrics."""

    @auth_required('token')
    @roles_required('examiner')
    def get(self):
        exams = Examination.query.all()
        result = []
        for e in exams:
            rubrics_data = [
                {
                    "id": r.id,
                    "criterion_name": r.criterion_name,
                    "max_marks": r.max_marks,
                    "weightage": r.weightage,
                    "description": r.description
                }
                for r in e.rubrics
            ]
            result.append({
                "id": e.id,
                "course_id": e.course_id,
                "course_name": e.course.name if e.course else "Unknown Course",
                "name": e.name,
                "exam_type": e.exam_type,
                "duration": e.duration,
                "max_marks": e.max_marks,
                "slot_creation_start": str(e.slot_creation_start) if e.slot_creation_start else None,
                "slot_creation_end": str(e.slot_creation_end) if e.slot_creation_end else None,
                "booking_start": str(e.booking_start) if e.booking_start else None,
                "booking_end": str(e.booking_end) if e.booking_end else None,
                "status": e.status,
                "rubrics": rubrics_data
            })
        return {"exams": result}


class ExaminerExamRubricsResource(Resource):
    """GET = Retrieve evaluation rubrics for an examination."""

    @auth_required('token')
    @roles_required('examiner')
    def get(self, exam_id):
        exam = Examination.query.get_or_404(exam_id)
        rubrics = [
            {
                "id": r.id,
                "criterion_name": r.criterion_name,
                "max_marks": r.max_marks,
                "weightage": r.weightage,
                "description": r.description
            }
            for r in exam.rubrics
        ]
        return {
            "examination_id": exam.id,
            "examination_name": exam.name,
            "max_marks": exam.max_marks,
            "rubrics": rubrics
        }


# Register all examiner resources
examiner_api.add_resource(ExaminerDashboardResource, '/dashboard')
examiner_api.add_resource(ExaminerExamListResource, '/exams')
examiner_api.add_resource(ExaminerExamRubricsResource, '/exams/<int:exam_id>/rubrics')
examiner_api.add_resource(ExaminerSlotListResource, '/slots')
examiner_api.add_resource(ExaminerSlotResource, '/slots/<int:slot_id>')
examiner_api.add_resource(ExaminerSlotBookingsResource, '/slots/<int:slot_id>/bookings')
examiner_api.add_resource(EvaluationSubmitResource, '/evaluations')
examiner_api.add_resource(SlotCompleteResource, '/slots/<int:slot_id>/complete')

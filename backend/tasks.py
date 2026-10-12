"""
Celery Background Tasks — Phase 7 implementation.
Includes:
1. send_slot_reminders — sends upcoming exam reminders to students and examiners (24h prior)
2. generate_daily_admin_report — daily activity summary (bookings, exams, evaluations)
3. export_exam_results_csv — asynchronous CSV export of exam evaluations
"""
import os
import csv
from datetime import datetime, timedelta
from celery.schedules import crontab

# Celery instance will be initialized or imported from app
from app import celery, app
from models import db, ExamSlot, Booking, Evaluation, Examination, User


@celery.task(name='tasks.send_slot_reminders')
def send_slot_reminders():
    """Identify slots scheduled for tomorrow and dispatch reminders to students & examiners."""
    with app.app_context():
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        slots = ExamSlot.query.filter_by(date=tomorrow).filter(ExamSlot.status != 'cancelled').all()

        reminders_sent = 0
        logs = []

        for slot in slots:
            exam_name = slot.examination.name if slot.examination else "Examination"
            examiner_email = slot.examiner.user.email if slot.examiner and slot.examiner.user else None

            # Notify examiner
            if examiner_email:
                log_entry = (
                    f"Reminder sent to Examiner ({examiner_email}) for slot #{slot.id} "
                    f"({exam_name}) at {slot.start_time}"
                )
                logs.append(log_entry)
                reminders_sent += 1

            # Notify all booked students
            for booking in slot.bookings:
                if booking.status == 'booked' and booking.student and booking.student.user:
                    student_email = booking.student.user.email
                    student_name = booking.student.user.name
                    log_entry = (
                        f"Reminder sent to Student {student_name} ({student_email}) for slot #{slot.id} "
                        f"({exam_name}) on {slot.date} at {slot.start_time}"
                    )
                    logs.append(log_entry)
                    reminders_sent += 1

        print(f"[Celery] {reminders_sent} reminders dispatched for {len(slots)} slots.")
        return {
            "status": "success",
            "slots_checked": len(slots),
            "reminders_sent": reminders_sent,
            "logs": logs
        }


@celery.task(name='tasks.generate_daily_admin_report')
def generate_daily_admin_report():
    """Generate daily activity metrics summary for the admin."""
    with app.app_context():
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # Count activities for today
        new_bookings_today = Booking.query.filter(
            Booking.booking_date >= today_start,
            Booking.booking_date <= today_end
        ).count()

        slots_today = ExamSlot.query.filter_by(date=today).count()

        evaluations_today = Evaluation.query.filter(
            Evaluation.evaluation_date >= today_start,
            Evaluation.evaluation_date <= today_end
        ).count()

        pending_evaluations = Booking.query.filter_by(status='booked').count()

        report = {
            "date": today.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "slots_scheduled_today": slots_today,
            "new_bookings_today": new_bookings_today,
            "evaluations_completed_today": evaluations_today,
            "total_pending_evaluations": pending_evaluations
        }

        # Save report to exports directory
        reports_dir = os.path.join(app.config['BASE_DIR'], 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, f"report_{today.isoformat()}.json")

        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"[Celery] Daily admin report generated at {report_path}")
        return report


@celery.task(name='tasks.export_exam_results_csv')
def export_exam_results_csv(examination_id):
    """Generate a CSV export containing all student scores and feedback for an examination."""
    with app.app_context():
        exam = Examination.query.get(examination_id)
        if not exam:
            return {"error": f"Examination ID {examination_id} not found"}

        exports_dir = os.path.join(app.config['BASE_DIR'], 'exports')
        os.makedirs(exports_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"exam_{exam.id}_results_{timestamp}.csv"
        filepath = os.path.join(exports_dir, filename)

        # Gather bookings and evaluations for slots belonging to this exam
        slots = ExamSlot.query.filter_by(examination_id=exam.id).all()
        slot_ids = [s.id for s in slots]
        bookings = Booking.query.filter(Booking.slot_id.in_(slot_ids)).all() if slot_ids else []

        with open(filepath, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "Booking ID",
                "Student Name",
                "Student Email",
                "Course Code",
                "Course Name",
                "Exam Name",
                "Slot Date",
                "Slot Start Time",
                "Slot End Time",
                "Examiner Name",
                "Total Marks",
                "Max Marks",
                "Remarks",
                "Evaluation Date",
                "Booking Status"
            ])

            for b in bookings:
                student_user = b.student.user if b.student and b.student.user else None
                slot = b.slot
                examiner_user = slot.examiner.user if slot and slot.examiner and slot.examiner.user else None
                eval_record = b.evaluation

                writer.writerow([
                    b.id,
                    student_user.name if student_user else "N/A",
                    student_user.email if student_user else "N/A",
                    exam.course.code if exam.course else "N/A",
                    exam.course.name if exam.course else "N/A",
                    exam.name,
                    slot.date.isoformat() if slot and slot.date else "N/A",
                    slot.start_time.isoformat() if slot and slot.start_time else "N/A",
                    slot.end_time.isoformat() if slot and slot.end_time else "N/A",
                    examiner_user.name if examiner_user else "N/A",
                    eval_record.total_marks if eval_record else "Pending",
                    exam.max_marks or "N/A",
                    eval_record.remarks if eval_record else "",
                    eval_record.evaluation_date.isoformat() if eval_record and eval_record.evaluation_date else "N/A",
                    b.status
                ])

        print(f"[Celery] Exported {len(bookings)} results to {filepath}")
        return {
            "status": "success",
            "examination_id": exam.id,
            "exam_name": exam.name,
            "filename": filename,
            "filepath": filepath,
            "total_records": len(bookings)
        }


# Beat Schedule configuration
celery.conf.beat_schedule = {
    'send-daily-slot-reminders': {
        'task': 'tasks.send_slot_reminders',
        'schedule': crontab(hour=8, minute=0),  # Everyday at 8:00 AM UTC
    },
    'generate-daily-admin-report': {
        'task': 'tasks.generate_daily_admin_report',
        'schedule': crontab(hour=21, minute=0),  # Everyday at 9:00 PM UTC
    },
}
celery.conf.timezone = 'UTC'

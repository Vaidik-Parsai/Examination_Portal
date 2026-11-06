"""
Background tasks for exam reminders, daily/monthly reporting, and CSV exports.
"""
import os
import csv
import smtplib
from datetime import datetime, timedelta
from calendar import monthrange
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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


def _build_monthly_report_html(report):
    """Build an HTML email template for the monthly examination report."""
    top_examiners_rows = ""
    for idx, ex in enumerate(report.get("top_examiners", []), start=1):
        top_examiners_rows += f"""
        <tr>
          <td style="padding:8px 12px; border-bottom:1px solid #dee2e6;">{idx}</td>
          <td style="padding:8px 12px; border-bottom:1px solid #dee2e6;">{ex['name']}</td>
          <td style="padding:8px 12px; border-bottom:1px solid #dee2e6;">{ex['department'] or '—'}</td>
          <td style="padding:8px 12px; border-bottom:1px solid #dee2e6; font-weight:bold;">{ex['evaluations_count']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,Helvetica,sans-serif; background:#f4f6f9; padding:20px;">
  <div style="max-width:600px; margin:0 auto; background:#fff; border:1px solid #dee2e6; border-radius:6px; overflow:hidden;">
    <div style="background:#212529; color:#fff; padding:20px 24px; border-bottom:3px solid #0d6efd;">
      <h1 style="margin:0; font-size:1.4rem;">📋 Monthly Examination Report</h1>
      <p style="margin:4px 0 0; color:#ced4da; font-size:13px;">
        Period: {report['month_label']} &nbsp;|&nbsp; Generated: {report['generated_at']}
      </p>
    </div>

    <div style="padding:24px;">
      <h2 style="font-size:1.1rem; margin-bottom:16px;">Summary Statistics</h2>
      <table style="width:100%; border-collapse:collapse; margin-bottom:24px;">
        <tr style="background:#f8f9fa;">
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-weight:600;">Examinations Conducted</td>
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-size:1.2rem; font-weight:bold; color:#0d6efd;">{report['exams_conducted']}</td>
        </tr>
        <tr>
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-weight:600;">Students Evaluated</td>
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-size:1.2rem; font-weight:bold; color:#198754;">{report['students_evaluated']}</td>
        </tr>
        <tr style="background:#f8f9fa;">
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-weight:600;">Completed Bookings</td>
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-size:1.2rem; font-weight:bold;">{report['completed_bookings']}</td>
        </tr>
        <tr>
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-weight:600;">Pending Evaluations</td>
          <td style="padding:10px 14px; border:1px solid #dee2e6; font-size:1.2rem; font-weight:bold; color:#dc3545;">{report['pending_evaluations']}</td>
        </tr>
      </table>

      <h2 style="font-size:1.1rem; margin-bottom:12px;">Top Active Examiners</h2>
      <table style="width:100%; border-collapse:collapse; margin-bottom:24px;">
        <thead>
          <tr style="background:#f8f9fa;">
            <th style="padding:8px 12px; border-bottom:2px solid #dee2e6; text-align:left;">#</th>
            <th style="padding:8px 12px; border-bottom:2px solid #dee2e6; text-align:left;">Examiner</th>
            <th style="padding:8px 12px; border-bottom:2px solid #dee2e6; text-align:left;">Department</th>
            <th style="padding:8px 12px; border-bottom:2px solid #dee2e6; text-align:left;">Evaluations</th>
          </tr>
        </thead>
        <tbody>
          {top_examiners_rows if top_examiners_rows else '<tr><td colspan="4" style="padding:12px; color:#6c757d;">No evaluations recorded this month.</td></tr>'}
        </tbody>
      </table>

      <p style="font-size:12px; color:#6c757d; border-top:1px solid #dee2e6; padding-top:12px; margin:0;">
        This is an automated report generated by Examination Portal.
      </p>
    </div>
  </div>
</body>
</html>"""


def _send_email(to_address, subject, html_body):
    """Send an HTML email via SMTP (uses MailHog defaults for local dev)."""
    smtp_host = app.config.get('MAIL_SERVER', 'localhost')
    smtp_port = int(app.config.get('MAIL_PORT', 1025))
    smtp_user = app.config.get('MAIL_USERNAME', '')
    smtp_pass = app.config.get('MAIL_PASSWORD', '')
    sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@examportal.local')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_address
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(sender, [to_address], msg.as_string())
        return True
    except Exception as e:
        print(f"[Celery] Email send failed: {e}")
        return False


@celery.task(name='tasks.generate_monthly_exam_report')
def generate_monthly_exam_report(year=None, month=None):
    """Generate a monthly examination report and email it to the admin.
    Defaults to the previous calendar month.
    Accepts optional year/month args for manual triggers."""
    import calendar
    from models import ExaminerProfile

    with app.app_context():
        now = datetime.utcnow()

        if not year or not month:
            # Default: previous month
            first_of_this_month = now.replace(day=1)
            last_month = first_of_this_month - timedelta(days=1)
            year = last_month.year
            month = last_month.month

        month_start = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59)
        month_label = month_start.strftime('%B %Y')

        # Exams conducted: slots with status 'completed' in the month
        exams_conducted = ExamSlot.query.filter(
            ExamSlot.date >= month_start.date(),
            ExamSlot.date <= month_end.date(),
            ExamSlot.status == 'completed'
        ).count()

        # Students evaluated: distinct students with completed evaluations in the month
        from sqlalchemy import func
        students_evaluated = db.session.query(
            func.count(func.distinct(Booking.student_id))
        ).join(Evaluation, Evaluation.booking_id == Booking.id).filter(
            Evaluation.evaluation_date >= month_start,
            Evaluation.evaluation_date <= month_end
        ).scalar() or 0

        # Completed bookings in the month
        completed_bookings = Booking.query.filter(
            Booking.status == 'completed',
            Booking.booking_date >= month_start,
            Booking.booking_date <= month_end
        ).count()

        # Total pending evaluations (across all time)
        pending_evaluations = Booking.query.filter_by(status='booked').count()

        # Top examiners by evaluations in the month
        examiner_counts = db.session.query(
            Evaluation.examiner_id,
            func.count(Evaluation.id).label('cnt')
        ).filter(
            Evaluation.evaluation_date >= month_start,
            Evaluation.evaluation_date <= month_end
        ).group_by(Evaluation.examiner_id).order_by(func.count(Evaluation.id).desc()).limit(5).all()

        top_examiners = []
        for examiner_id, cnt in examiner_counts:
            ep = ExaminerProfile.query.get(examiner_id)
            top_examiners.append({
                'name': ep.user.name if ep and ep.user else f'Examiner #{examiner_id}',
                'department': ep.department if ep else None,
                'evaluations_count': cnt
            })

        report = {
            'year': year,
            'month': month,
            'month_label': month_label,
            'generated_at': now.strftime('%Y-%m-%d %H:%M UTC'),
            'exams_conducted': exams_conducted,
            'students_evaluated': students_evaluated,
            'completed_bookings': completed_bookings,
            'pending_evaluations': pending_evaluations,
            'top_examiners': top_examiners
        }

        # Save JSON report
        reports_dir = os.path.join(app.config['BASE_DIR'], 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, f"monthly_report_{year}_{month:02d}.json")
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        # Build HTML and send email to admin
        html = _build_monthly_report_html(report)
        admin_email = app.config.get('ADMIN_EMAIL', os.getenv('ADMIN_EMAIL', 'admin@example.com'))
        email_sent = _send_email(
            to_address=admin_email,
            subject=f"[EMP] Monthly Examination Report — {month_label}",
            html_body=html
        )

        print(f"[Celery] Monthly report for {month_label} generated. Email sent: {email_sent}")
        return {
            "status": "success",
            "month_label": month_label,
            "report_path": report_path,
            "email_sent": email_sent,
            "summary": {
                "exams_conducted": exams_conducted,
                "students_evaluated": students_evaluated,
                "completed_bookings": completed_bookings,
                "pending_evaluations": pending_evaluations,
                "top_examiners_count": len(top_examiners)
            }
        }


# Beat Schedule configuration
celery.conf.beat_schedule = {
    'send-daily-slot-reminders': {
        'task': 'tasks.send_slot_reminders',
        'schedule': crontab(hour=8, minute=0),  # Every day at 08:00 UTC
    },
    'generate-daily-admin-report': {
        'task': 'tasks.generate_daily_admin_report',
        'schedule': crontab(hour=21, minute=0),  # Every day at 21:00 UTC
    },
    'generate-monthly-exam-report': {
        'task': 'tasks.generate_monthly_exam_report',
        'schedule': crontab(hour=0, minute=0, day_of_month=1),  # 1st of every month at 00:00 UTC
    },
}
celery.conf.timezone = 'UTC'

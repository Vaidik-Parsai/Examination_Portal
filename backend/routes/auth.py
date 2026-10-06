"""
Auth Routes — handles student self-registration.
Login/logout are provided automatically by Flask-Security at /api/auth/login and /api/auth/logout.
"""
import uuid
from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_security.utils import hash_password

from models import db, StudentProfile

# Step 1: Create a Blueprint (a mini-app for auth routes)
auth_bp = Blueprint('auth', __name__)

# Step 2: Create a Flask-RESTful Api tied to THIS blueprint (not the main app)
auth_api = Api(auth_bp)

# Step 3: Define Resources as usual
class StudentRegisterResource(Resource):
    """Only students can self-register. Admin creates examiners."""
    def post(self):
        # We import here to avoid circular imports (app.py imports routes, routes need app's datastore)
        from app import user_datastore

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password or not name:
            return {"message": "Email, password, and name are required"}, 400

        if user_datastore.find_user(email=email):
            return {"message": "Email already registered"}, 400

        user = user_datastore.create_user(
            email=email,
            password=hash_password(password),
            name=name,
            roles=['student'],
            fs_uniquifier=uuid.uuid4().hex
        )
        db.session.commit()

        student_profile = StudentProfile(user_id=user.id)
        db.session.add(student_profile)
        db.session.commit()

        return {"message": "Student registered successfully"}, 201

# Step 4: Register the Resource to an endpoint on THIS api
auth_api.add_resource(StudentRegisterResource, '/api/auth/student/register')

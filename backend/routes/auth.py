"""
Auth Routes — handles login, logout, and student registration.
Provides direct token-based authentication at /api/auth/login.
"""
import uuid
from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_security.utils import hash_password, verify_password

from models import db, StudentProfile

# Step 1: Create Blueprint
auth_bp = Blueprint('auth', __name__)
auth_api = Api(auth_bp)


class UserLoginResource(Resource):
    """Direct, reliable token login without session cookie interference."""
    def post(self):
        from app import user_datastore

        data = request.get_json(force=True)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {"message": "Email and password are required"}, 400

        user = user_datastore.find_user(email=email)
        if not user or not verify_password(password, user.password):
            return {"message": "Invalid email or password"}, 400

        if not user.active:
            return {"message": "Account is deactivated"}, 403

        # Generate auth token
        token = user.get_auth_token()
        roles = [r.name for r in user.roles]

        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "roles": roles,
                "authentication_token": token
            }
        }, 200


class UserLogoutResource(Resource):
    """Client clears local token; returns success message."""
    def post(self):
        return {"message": "Logged out successfully"}, 200


class StudentRegisterResource(Resource):
    """Only students can self-register. Admin creates examiners."""
    def post(self):
        from app import user_datastore

        data = request.get_json(force=True)
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


# Register Resources
auth_api.add_resource(UserLoginResource, '/api/auth/login')
auth_api.add_resource(UserLogoutResource, '/api/auth/logout')
auth_api.add_resource(StudentRegisterResource, '/api/auth/student/register')

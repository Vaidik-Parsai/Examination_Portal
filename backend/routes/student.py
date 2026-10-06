"""
Student Routes — placeholder for Phase 5.
All endpoints protected by @roles_required('student').
"""
from flask import Blueprint
from flask_restful import Api, Resource
from flask_security import auth_required, roles_required

# Create Blueprint and Api
student_bp = Blueprint('student', __name__)
student_api = Api(student_bp)

class StudentDashboardResource(Resource):
    @auth_required('token')
    @roles_required('student')
    def get(self):
        return {"message": "Welcome to the Student Dashboard!"}

# Register Resources
student_api.add_resource(StudentDashboardResource, '/api/student/dashboard')

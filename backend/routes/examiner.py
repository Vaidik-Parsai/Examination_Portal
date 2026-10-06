"""
Examiner Routes — placeholder for Phase 4.
All endpoints protected by @roles_required('examiner').
"""
from flask import Blueprint
from flask_restful import Api, Resource
from flask_security import auth_required, roles_required

# Create Blueprint and Api
examiner_bp = Blueprint('examiner', __name__)
examiner_api = Api(examiner_bp)

class ExaminerDashboardResource(Resource):
    @auth_required('token')
    @roles_required('examiner')
    def get(self):
        return {"message": "Welcome to the Examiner Dashboard!"}

# Register Resources
examiner_api.add_resource(ExaminerDashboardResource, '/api/examiner/dashboard')

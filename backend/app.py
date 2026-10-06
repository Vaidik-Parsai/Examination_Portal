"""
app.py — The main entry point.
Responsibilities: Config, extension init, blueprint registration, DB seeding.
All route logic lives in the routes/ folder.
"""
import os
from flask import Flask
from flask_restful import Api, Resource
from flask_caching import Cache
from celery import Celery
from flask_security import Security, SQLAlchemyUserDatastore

from models import db, User, Role, init_roles_and_admin

# ==========================================
# CONFIG
# ==========================================
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key-change-in-prod')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, '..', 'examination.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Security settings
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', 'somesalt')
    WTF_CSRF_ENABLED = False
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True
    SECURITY_FLASH_MESSAGES = False
    SECURITY_URL_PREFIX = '/api/auth'
    SECURITY_REDIRECT_BEHAVIOR = 'spa'

    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = REDIS_URL
    CELERY_BROKER_URL = REDIS_URL
    result_backend = REDIS_URL

# ==========================================
# CREATE APP AND EXTENSIONS
# ==========================================
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
cache = Cache(app)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# ==========================================
# A simple root route (no blueprint needed)
# ==========================================
class HomeResource(Resource):
    def get(self):
        return {"status": "success", "message": "Welcome to the Examination Portal API!"}

home_api = Api(app)
home_api.add_resource(HomeResource, '/')

# ==========================================
# REGISTER BLUEPRINTS (one per role)
# ==========================================
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.examiner import examiner_bp
from routes.student import student_bp

app.register_blueprint(auth_bp)      # /api/auth/student/register
app.register_blueprint(admin_bp)     # /api/admin/...
app.register_blueprint(examiner_bp)  # /api/examiner/...
app.register_blueprint(student_bp)   # /api/student/...

# ==========================================
# DB INIT AND RUN
# ==========================================
def init_db():
    with app.app_context():
        db.create_all()
        init_roles_and_admin(user_datastore)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

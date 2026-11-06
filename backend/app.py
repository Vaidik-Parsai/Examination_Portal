import os
from flask import Flask
from flask_restful import Api, Resource
from flask_caching import Cache
from celery import Celery
from flask_security import Security, SQLAlchemyUserDatastore

from models import db, User, Role, init_roles_and_admin
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.examiner import examiner_bp
from routes.student import student_bp


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key-change-in-prod')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, '..', 'examination.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', 'somesalt')
    WTF_CSRF_ENABLED = False
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True
    SECURITY_FLASH_MESSAGES = False
    SECURITY_URL_PREFIX = '/api/security'
    SECURITY_REDIRECT_BEHAVIOR = 'spa'

    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_ALWAYS_EAGER', 'True').lower() == 'true'

    # Mail config — defaults to MailHog for local dev (smtp port 1025)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 1025))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@examportal.local')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')


app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
cache = Cache(app)
celery = Celery(app.name)
celery.conf.update(
    broker_url=app.config['CELERY_BROKER_URL'],
    result_backend=app.config['CELERY_RESULT_BACKEND'],
    task_always_eager=app.config['CELERY_TASK_ALWAYS_EAGER']
)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Load background tasks
import tasks


class HomeResource(Resource):
    def get(self):
        return {"status": "success", "message": "Examination Portal API"}


home_api = Api(app)
home_api.add_resource(HomeResource, '/')

# Register role blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(examiner_bp)
app.register_blueprint(student_bp)


def init_db():
    with app.app_context():
        db.create_all()
        init_roles_and_admin(user_datastore)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

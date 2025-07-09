from flask import Flask
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
from flask_mail import Mail
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from bson.objectid import ObjectId
from app.models import User


mail = Mail()
mongo = PyMongo()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # redirect if not logged in
login_manager.login_message_category = 'info'


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # MongoDB URI + Database name
    mongo_uri = os.getenv('MONGO_URI')
    db_name = os.getenv('DB_NAME')

    if not mongo_uri or not db_name:
        raise ValueError("❌ MONGO_URI or DB_NAME is not set in environment.")

    app.config['MONGO_URI'] = f"{mongo_uri}{db_name}?retryWrites=true&w=majority"

    # Email Config
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    # Initialize extensions
    mail.init_app(app)
    bcrypt.init_app(app)
    mongo.init_app(app)
    login_manager.init_app(app)


    # Register blueprints
    from .routes.main_routes import main_bp
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    @login_manager.user_loader
    def load_user(user_id):
        user_doc = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return User(user_doc) if user_doc else None
    # Inject current year into all templates
    @app.context_processor
    def inject_now():
        return {'current_year': datetime.utcnow().year}
    
    return app

from flask import Flask
from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from app.models import User
from config import Config
from app.scrapers.odibets_scraper import scrape_odibets_odds  # ✅ make sure path is correct

# Extensions
mail = Mail()
mongo = PyMongo()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    mail.init_app(app)
    mongo.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from .routes.main_routes import main_bp
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # User loader for login
    @login_manager.user_loader
    def load_user(user_id):
        user_doc = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return User(user_doc) if user_doc else None

    # Context processor
    @app.context_processor
    def inject_now():
        return {'current_year': datetime.utcnow().year}

    # ✅ Scheduler for scraping Odibets odds every 10 mins
    def start_scheduler():
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(func=scrape_odibets_odds, trigger='interval', minutes=10)
        scheduler.start()
        print("🕒 Scheduler started: scraping every 10 minutes")

    # ✅ Start the scheduler after app is ready
    with app.app_context():
        start_scheduler()

    return app

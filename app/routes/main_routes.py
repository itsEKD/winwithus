# app/routes/main_routes.py

from flask import Blueprint, render_template
from app import mongo
from app.models.tip import Tip
from app.models.post import Post

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    latest_tips = mongo.db.tips.find().sort("created_at", -1).limit(5)
    tips = [Tip(tip) for tip in latest_tips]

    latest_posts = mongo.db.posts.find().sort("created_at", -1).limit(5)
    posts = [Post(p) for p in latest_posts]

    return render_template("home.html", tips=tips, posts=posts)

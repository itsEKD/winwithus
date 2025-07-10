# app/routes/main_routes.py

from flask import Blueprint, render_template, redirect, flash, url_for
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

@main_bp.route('/blogs')
def blogs():
    posts = Post.get_all(mongo)
    return render_template('blogs.html', posts=posts, title="Blog Posts")

@main_bp.route('/posts/<post_id>')
def view_post(post_id):
    post = Post.get_by_id(mongo, post_id)
    if not post:
        flash("Post not found.", "warning")
        return redirect(url_for('main.blogs'))

    other_posts = Post.get_all(mongo)
    return render_template("view_post.html", post=post, other_posts=other_posts)

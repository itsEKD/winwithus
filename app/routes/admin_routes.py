from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import mongo
from bson.objectid import ObjectId
from app.forms.tip_forms import TipForm
from app.forms.post_form import PostForm
from app.models.tip import Tip
from datetime import datetime
from app.models import Post
import uuid, os 

UPLOAD_FOLDER = 'app/static/uploads/posts'

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(func):
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Access denied: Admins only.", "danger")
            return redirect(url_for('main.home'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    # Counts for dashboard tiles
    user_count = mongo.db.users.count_documents({})
    tip_count = mongo.db.tips.count_documents({})
    post_count = mongo.db.posts.count_documents({})
    tipster_count = mongo.db.users.count_documents({'role': 'tipster'})

    return render_template(
        'admin/dashboard.html',
        title="Admin Dashboard",
        user_count=user_count,
        tip_count=tip_count,
        post_count=post_count,
        tipster_count=tipster_count
    )


@admin_bp.route('/tipster/dashboard')
@login_required
def tipster_dashboard():
    if current_user.role != 'tipster':
        flash("Access denied: Tipsters only.", "danger")
        return redirect(url_for('main.home'))

    # Get all tips posted by the current tipster
    tips_cursor = mongo.db.tips.find({'tipster_id': str(current_user.id)}).sort('created_at', -1)
    tips = [Tip(tip) for tip in tips_cursor]

    return render_template('admin/tipster_dashboard.html', tips=tips, title="Tipster Dashboard")


@admin_bp.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.home'))

    users = mongo.db.users.find()
    return render_template('admin/manage_users.html', users=users, title="Manage Users")


@admin_bp.route('/users/<user_id>/update_status', methods=['POST'])
@login_required
def update_tipster_status(user_id):
    if not current_user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('main.home'))

    new_status = request.form.get("status")  # 'approved' or 'rejected'

    if new_status in ["approved", "rejected"]:
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"tipster_status": new_status}}
        )
        flash(f"User status updated to '{new_status}'.", "success")
    else:
        flash("Invalid status update.", "warning")

    return redirect(url_for('admin.manage_users'))



@admin_bp.route('/users/<user_id>/update-role', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not current_user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('main.home'))

    role = request.form.get('role')
    tipster_status = request.form.get('tipster_status')

    update_fields = {'role': role}
    if role == 'tipster':
        update_fields['tipster_status'] = tipster_status or 'pending'
    else:
        update_fields['tipster_status'] = None

    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )

    flash("User updated successfully.", "success")
    return redirect(url_for('admin.manage_users'))




from flask import request
from datetime import datetime

@admin_bp.route('/tips/new', methods=['GET', 'POST'])
@login_required
def create_tip():
    if not current_user.is_admin and current_user.role != 'tipster':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    form = TipForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            match_date_str = request.form.get("match_date")  # from raw input
            try:
                match_date = datetime.strptime(match_date_str, '%Y-%m-%dT%H:%M')
            except (ValueError, TypeError):
                flash("Invalid match date format.", "danger")
                return render_template('admin/tips/create_tip.html', form=form, title="Post Tip")

            tip_data = {
                'title': form.title.data,
                'description': form.description.data,
                'odds': form.odds.data,
                'sport': form.sport.data,
                'match_date': match_date,
                'posted_by': current_user.id,
                'tipster_name': current_user.username,
                'created_at': datetime.utcnow(),
                'tipster_id': str(current_user.id)
            }
            tip = Tip(tip_data)
            tip.save(mongo)
            flash("Betting tip posted!", "success")
            return redirect(url_for('admin.tipster_dashboard'))

    return render_template('admin/tips/create_tip.html', form=form, title="Post Tip")



@admin_bp.route('/tips', methods=['GET'])
@login_required
def manage_tips():
    if not current_user.is_admin and current_user.role != 'tipster':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    if current_user.is_admin:
        tips = Tip.get_all(mongo)  # All tips
    else:
        # Only tips by this tipster
        tips = mongo.db.tips.find({'posted_by': current_user.id}).sort('created_at', -1)
        tips = [Tip(tip) for tip in tips]

    return render_template('admin/tips/manage_tips.html', tips=tips, title="Manage Betting Tips")


@admin_bp.route('/tips/<tip_id>/delete', methods=['POST'])
@login_required
def delete_tip(tip_id):
    if not current_user.is_admin and current_user.role != 'tipster':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    # Only allow deletion of tips the user owns (if not admin)
    if not current_user.is_admin:
        tip = Tip.get_by_id(mongo, tip_id)
        if not tip or str(tip.posted_by) != str(current_user.id):
            flash("You are not authorized to delete this tip.", "danger")
            return redirect(url_for('admin.manage_tips'))

    Tip.delete(tip_id, mongo)  # 🛠 Pass mongo explicitly
    flash("Tip deleted successfully.", "success")
    return redirect(url_for('admin.manage_tips'))




@admin_bp.route('/tips/<tip_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tip(tip_id):
    tip = Tip.get_by_id(mongo, tip_id)
    if not tip:
        flash("Tip not found.", "warning")
        return redirect(url_for('admin.manage_tips'))

    if not current_user.is_admin and str(current_user.id) != tip.tipster_id:
        flash("You are not authorized to edit this tip.", "danger")
        return redirect(url_for('main.home'))

    form = TipForm()

    if request.method == 'GET':
        form.title.data = tip.title
        form.description.data = tip.description
        form.odds.data = tip.odds
        form.sport.data = tip.sport

    if form.validate_on_submit():
        # Parse datetime-local field from raw form input
        raw_match_date = request.form.get("match_date")
        try:
            match_date = datetime.strptime(raw_match_date, "%Y-%m-%dT%H:%M")
        except (ValueError, TypeError):
            flash("Invalid date format. Please use the datetime picker.", "danger")
            return render_template('admin/tips/edit_tip.html', form=form, tip=tip, title="Edit Tip")

        updates = {
            'title': form.title.data,
            'description': form.description.data,
            'odds': form.odds.data,
            'sport': form.sport.data,
            'match_date': match_date
        }
        Tip.update(mongo, tip_id, updates)
        flash("Tip updated successfully.", "success")
        return redirect(url_for('admin.manage_tips'))

    return render_template('admin/tips/edit_tip.html', form=form, tip=tip, title="Edit Tip")

@admin_bp.route('/admin/posts')
@login_required
def manage_posts():
    if not current_user.is_admin:
        abort(403)
    
    post_docs = mongo.db.posts.find().sort("created_at", -1)
    posts = [Post(doc) for doc in post_docs]
    return render_template('admin/manage_posts.html', posts=posts, title="Manage Blog Posts")


# CREATE POST
@admin_bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            ext = os.path.splitext(form.image.data.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            form.image.data.save(os.path.join(UPLOAD_FOLDER, filename))

        post_data = {
            "title": form.title.data,
            "content": form.content.data,
            "author": current_user.username,
            "created_at": None,
            "image_filename": filename
        }
        post = Post(post_data)
        post.save(mongo)
        flash("Post published successfully.", "success")
        return redirect(url_for('admin.manage_posts'))

    return render_template('admin/posts/create_post.html', form=form, title="New Blog Post")

# EDIT POST
@admin_bp.route('/posts/<post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.get_by_id(post_id, mongo)
    if not post:
        flash("Post not found.", "warning")
        return redirect(url_for('admin.manage_posts'))

    form = PostForm()
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    if form.validate_on_submit():
        updates = {
            "title": form.title.data,
            "content": form.content.data,
        }

        if form.image.data:
            ext = os.path.splitext(form.image.data.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            form.image.data.save(os.path.join(UPLOAD_FOLDER, filename))
            updates['image_filename'] = filename

        Post.update(post_id, updates, mongo)
        flash("Post updated.", "success")
        return redirect(url_for('admin.manage_posts'))

    return render_template('admin/posts/edit_post.html', form=form, post=post, title="Edit Blog Post")

@admin_bp.route('/admin/posts/<post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    if not current_user.is_admin:
        abort(403)
    mongo.db.posts.delete_one({'_id': ObjectId(post_id)})
    flash('Post deleted successfully.', 'info')
    return redirect(url_for('admin.manage_posts'))

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import mongo
from bson.objectid import ObjectId
from app.forms.tip_forms import TipForm
from app.forms.post_form import PostForm
from app.models.tip import Tip
from datetime import datetime
from app.models import Post



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
    return render_template('admin/dashboard.html', title="Admin Dashboard")
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
        if form.validate():
            match_date_str = request.form.get('match_date')

            try:
                match_date = datetime.strptime(match_date_str, "%Y-%m-%dT%H:%M")
            except (ValueError, TypeError):
                flash("Invalid date format. Please use the datetime picker.", "danger")
                return render_template('admin/tips/create_tip.html', form=form, title="Post Tip")

            tip_data = {
                'title': form.title.data,
                'description': form.description.data,
                'odds': form.odds.data,
                'sport': form.sport.data,
                'match_date': match_date,
                'posted_by': current_user.id,
                'tipster_name': current_user.username,
                'created_at': datetime.utcnow()
            }

            tip = Tip(tip_data)
            tip.save(mongo)
            flash("Betting tip posted!", "success")
            return redirect(url_for('admin.manage_tips'))
        else:
            flash("Please correct the errors in the form.", "danger")

    return render_template('admin/tips/create_tip.html', form=form, title="Post Tip")


@admin_bp.route('/tips', methods=['GET'])
@login_required
def manage_tips():
    if not current_user.is_admin and current_user.role != 'tipster':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    tips = Tip.get_all(mongo)  # Pass mongo as argument
    return render_template('admin/tips/manage_tips.html', tips=tips, title="Manage Betting Tips")

@admin_bp.route('/tips/<tip_id>/delete', methods=['POST'])
@login_required
def delete_tip(tip_id):
    if not current_user.is_admin and current_user.role != 'tipster':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    Tip.delete(tip_id)
    flash("Tip deleted successfully.", "success")
    return redirect(url_for('admin.manage_tips'))
@admin_bp.route('/tips/<tip_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tip(tip_id):
    tip = Tip.get_by_id(mongo, tip_id)
    if not tip:
        flash("Tip not found.", "warning")
        return redirect(url_for('admin.manage_tips'))

    # Only allow the tip owner or admin to edit
    if not current_user.is_admin and str(current_user.id) != tip.tipster_id:
        flash("You are not authorized to edit this tip.", "danger")
        return redirect(url_for('main.home'))

    form = TipForm()

    if request.method == 'GET':
        form.title.data = tip.title
        form.description.data = tip.description
        form.odds.data = tip.odds
        form.sport.data = tip.sport
        form.match_date.data = tip.match_date

    if form.validate_on_submit():
        updates = {
            'title': form.title.data,
            'description': form.description.data,
            'odds': form.odds.data,
            'sport': form.sport.data,
            'match_date': form.match_date.data
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


@admin_bp.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def create_post():
    if not current_user.is_admin:
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        new_post = {
            'title': form.title.data,
            'content': form.content.data,
            'author': current_user.username,
            'created_at': datetime.utcnow()
        }
        mongo.db.posts.insert_one(new_post)
        flash('Post created successfully.', 'success')
        return redirect(url_for('admin.manage_posts'))
    
    return render_template('admin/post_form.html', form=form, title="Create Post")


@admin_bp.route('/admin/posts/<post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    if not current_user.is_admin:
        abort(403)

    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    if not post:
        abort(404)

    form = PostForm(data=post)
    if form.validate_on_submit():
        updated_data = {
            'title': form.title.data,
            'content': form.content.data,
        }
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {'$set': updated_data})
        flash('Post updated successfully.', 'success')
        return redirect(url_for('admin.manage_posts'))

    return render_template('admin/post_form.html', form=form, title="Edit Post")

@admin_bp.route('/admin/posts/<post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    if not current_user.is_admin:
        abort(403)
    mongo.db.posts.delete_one({'_id': ObjectId(post_id)})
    flash('Post deleted successfully.', 'info')
    return redirect(url_for('admin.manage_posts'))

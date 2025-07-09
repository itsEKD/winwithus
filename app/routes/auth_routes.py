from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth_forms import RegisterForm, LoginForm, ResendConfirmationForm, ResetPasswordForm, RequestResetForm
from app import mongo, bcrypt, mail
from app.models import User
from bson.objectid import ObjectId
from flask_mail import Message
from app.utils.token import generate_confirmation_token, confirm_token, generate_reset_token, verify_reset_token
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ========== REGISTER ==========
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = mongo.db.users.find_one({'email': form.email.data})
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # By default, all new users are regular users (not tipsters)
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_pw,
            'is_admin': False,
            'is_confirmed': False,
            'role': 'user',                 # Role can be 'user' or 'tipster'
            'tipster_status': None,        # Will be set when user applies
            'created_at': datetime.utcnow()
        }

        mongo.db.users.insert_one(user_data)
        send_confirmation_email(user_data['email'])

        flash('Account created! Please check your email to confirm your account.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title="Register")



# ========== EMAIL CONFIRMATION ==========
def send_confirmation_email(user_email):
    token = generate_confirmation_token(user_email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('auth/confirm_email.html', confirm_url=confirm_url)

    msg = Message("Confirm Your Email - WinWithUs", recipients=[user_email])
    msg.html = html
    mail.send(msg)

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    user = mongo.db.users.find_one({'email': email})
    if not user:
        flash('User not found.', 'danger')
    elif user.get('is_confirmed'):
        flash('Account already confirmed. Please login.', 'info')
    else:
        mongo.db.users.update_one({'email': email}, {'$set': {'is_confirmed': True}})
        flash('Your email has been confirmed!', 'success')

    return redirect(url_for('auth.login'))


# ========== LOGIN ==========
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user_doc = mongo.db.users.find_one({'email': form.email.data})
        if user_doc and bcrypt.check_password_hash(user_doc['password'], form.password.data):

            if not user_doc.get('is_confirmed'):
                flash('Please confirm your email before logging in.', 'warning')
                return redirect(url_for('auth.login'))

            user = User(user_doc)
            login_user(user)
            flash('Login successful!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form, title="Login")

@auth_bp.route('/resend-confirmation', methods=['GET', 'POST'])
def resend_confirmation():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = ResendConfirmationForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({'email': form.email.data})
        if not user:
            flash('No account found with that email.', 'danger')
        elif user.get('is_confirmed'):
            flash('This account is already confirmed. You can log in.', 'info')
        else:
            send_confirmation_email(user['email'])
            flash('A new confirmation email has been sent.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/resend_confirmation.html', form=form, title="Resend Confirmation")



# ========== REQUEST RESET ==========
@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({'email': form.email.data})
        if user:
            send_password_reset_email(user['email'])
        flash('If your email is registered, you’ll receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_request.html', form=form, title="Reset Password")

# ========== EMAIL SENDER ==========
def send_password_reset_email(user_email):
    token = generate_reset_token(user_email)
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    html = render_template('auth/reset_email.html', reset_url=reset_url)

    msg = Message("Reset Your Password - WinWithUs", recipients=[user_email])
    msg.html = html
    mail.send(msg)

# ========== RESET TOKEN FORM ==========
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    email = verify_reset_token(token)
    if not email:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mongo.db.users.update_one({'email': email}, {'$set': {'password': hashed_pw}})
        flash('Your password has been updated. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_token.html', form=form, title="Set New Password")


# ========== LOGOUT ==========
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

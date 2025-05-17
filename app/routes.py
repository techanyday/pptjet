import os
from functools import wraps
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, login_user, logout_user, current_user
from app.models import User
from app import db

main = Blueprint('main', __name__)

PLANS = {
    'free': {'name': 'Free Plan', 'price': 0, 'presentations': 3},
    'creator': {'name': 'Creator Plan', 'price': 299, 'presentations': 20},
    'pro': {'name': 'Pro Plan', 'price': 499, 'presentations': 50}
}

# ➡ Add the missing login route
@main.route('/login')
def login():
    return "<h3>Login Page Placeholder</h3>"

def check_subscription(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.pricing'))

        if current_user.presentations_remaining <= 0:
            flash('You have reached your presentation limit. Please upgrade your plan.', 'error')
            return redirect(url_for('main.pricing'))

        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def home():
    return redirect(url_for('main.dashboard'))

@main.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/generate_presentation', methods=['POST'])
@login_required
def generate_presentation():
    if current_user.presentations_remaining <= 0:
        return jsonify({
            'error': 'limit_reached',
            'message': 'You have reached your presentation limit. Please upgrade your plan.'
        }), 403

    current_user.presentations_remaining -= 1
    db.session.commit()

    return jsonify({
        'message': 'Presentation generated successfully.',
        'presentations_remaining': current_user.presentations_remaining
    }), 200

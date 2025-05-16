import os
from functools import wraps
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, login_user, logout_user, current_user
from app.models import User
from app import db

main = Blueprint('main', __name__)

# Pricing plans configuration
PLANS = {
    'free': {
        'name': 'Free Plan',
        'price': 0,  # in cents
        'presentations': 3
    },
    'creator': {
        'name': 'Creator Plan',
        'price': 299,  # in cents
        'presentations': 20
    },
    'pro': {
        'name': 'Pro Plan',
        'price': 499,  # in cents
        'presentations': 50
    }
}

# Simple decorator to check presentations remaining from DB model
def check_subscription(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.pricing'))

        if current_user.presentations_remaining <= 0:
            flash('You have reached your presentation limit. Please upgrade your plan to continue.', 'error')
            return redirect(url_for('main.pricing'))

        return f(*args, **kwargs)
    return decorated_function

# Serve template image route
@main.route('/static/images/templates/<template>.jpg')
def serve_template_image(template):
    image_path = os.path.join('images', 'templates', f'{template}.jpg')
    return send_from_directory(current_app.static_folder, image_path, mimetype='image/jpeg')

GENERATED_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated'))

@main.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    plan = request.form.get('plan')
    if plan not in PLANS:
        return jsonify({'error': 'Invalid plan'}), 400

    plan_data = PLANS[plan]
    # Setup Paystack integration here (omitted for brevity)

    # After successful payment simulation:
    current_user.presentations_remaining = PLANS[plan]['presentations']
    db.session.commit()

    flash(f'Your plan has been upgraded to {PLANS[plan]["name"]}.')
    return redirect(url_for('main.dashboard'))

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

    # Place actual generation logic here

    current_user.presentations_remaining -= 1
    db.session.commit()

    return jsonify({
        'message': 'Presentation generated successfully.',
        'presentations_remaining': current_user.presentations_remaining
    }), 200

# Add your other routes here (auth, payment callback, etc.)

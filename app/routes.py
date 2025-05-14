import os
import json
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, session, jsonify
import requests
from functools import wraps
from flask_login import login_required, login_user, logout_user, current_user
from app.utils.ppt_generator import PPTGenerator
from app.models import User
from app import users_db

# Google OAuth 2.0 endpoints
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

bp = Blueprint("main", __name__)

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

def check_subscription(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.pricing'))
        # Here you would check if the user has an active subscription
        # and if they haven't exceeded their monthly limit
        return f(*args, **kwargs)
    return decorated_function

# Template image routes
@bp.route('/static/images/templates/<template>.jpg')
def serve_template_image(template):
    image_path = os.path.join('images', 'templates', f'{template}.jpg')
    return send_from_directory(current_app.static_folder, image_path, mimetype='image/jpeg')

# Get the absolute path to the generated directory
GENERATED_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated'))

@bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    plan = request.form.get('plan')
    if plan not in PLANS:
        return jsonify({'error': 'Invalid plan'}), 400

    plan_data = PLANS[plan]
    
    # Initialize Paystack transaction
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {os.environ.get("PAYSTACK_SECRET_KEY")}',
        'Content-Type': 'application/json'
    }
    data = {
        'email': current_user.email,
        'amount': plan_data['price'],  # amount in kobo (Nigerian currency)
        'callback_url': url_for('main.payment_callback', _external=True),
        'metadata': {
            'plan_id': plan,
            'user_id': current_user.id
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        if result['status']:
            # Store the reference in session for verification
            session['payment_reference'] = result['data']['reference']
            return redirect(result['data']['authorization_url'])
        else:
            flash('Could not initialize payment. Please try again.', 'error')
            return redirect(url_for('main.pricing'))

    except Exception as e:
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('main.pricing'))

@bp.route('/payment/callback')
@login_required
def payment_callback():
    reference = request.args.get('reference')
    if not reference or reference != session.get('payment_reference'):
        flash('Invalid payment reference', 'error')
        return redirect(url_for('main.pricing'))

    # Verify the transaction
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {
        'Authorization': f'Bearer {os.environ.get("PAYSTACK_SECRET_KEY")}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result['status'] and result['data']['status'] == 'success':
            # Get the plan from metadata
            metadata = result['data']['metadata']
            plan_id = metadata['plan_id']

            # Here you would update the user's subscription in your database
            # For now, we'll just show a success message
            flash(f'Successfully subscribed to {PLANS[plan_id]["name"]}!', 'success')
            return redirect(url_for('main.generate'))
        else:
            flash('Payment verification failed', 'error')
            return redirect(url_for('main.pricing'))

    except Exception as e:
        flash('Could not verify payment', 'error')
        return redirect(url_for('main.pricing'))
os.makedirs(GENERATED_FOLDER, exist_ok=True)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@bp.route("/")
def index():
    return render_template('index.html', user=current_user)

@bp.route("/privacy")
def privacy():
    return render_template('privacy.html', user=current_user, current_date='May 13, 2025')

@bp.route("/terms")
def terms():
    return render_template('terms.html', user=current_user, current_date='May 13, 2025')

@bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Get Google's OAuth 2.0 endpoints
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Use library to construct the request for Google login
    client = current_app.config['OAUTH_CLIENT']
    if request.host.startswith('localhost'):
        redirect_uri = 'http://localhost:5000/login/callback'
    else:
        redirect_uri = 'https://pptjet-dev.onrender.com/login/callback'
    
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=redirect_uri,
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@bp.route("/login/callback")
def callback():
    # Get authorization code Google sent back
    code = request.args.get("code")
    if not code:
        return "Error: No code provided", 400

    # Get Google's OAuth 2.0 endpoints
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens
    client = current_app.config['OAUTH_CLIENT']
    if request.host.startswith('localhost'):
        redirect_uri = 'http://localhost:5000/login/callback'
    else:
        redirect_uri = 'https://pptjet-dev.onrender.com/login/callback'

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=redirect_uri,
        code=code
    )
    # Get client credentials from the OAuth client config
    client = current_app.config['OAUTH_CLIENT']
    client_secrets = {
        "web": {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        }
    }
    
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(client_secrets["web"]["client_id"], client_secrets["web"]["client_secret"]),
    )

    # Parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Get user info from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["given_name"]
        picture = userinfo_response.json()["picture"]

        # Create a user in our db with the information provided by Google
        user_data = {
            "id": unique_id,
            "name": users_name,
            "email": users_email,
            "profile_pic": picture
        }
        users_db[unique_id] = user_data
        user = User(
            id_=unique_id,
            name=users_name,
            email=users_email,
            profile_pic=picture
        )

        # Begin user session by logging the user in
        login_user(user)

        # Send user back to homepage
        return redirect(url_for('main.index'))
    else:
        return "User email not available or not verified by Google.", 400

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    if request.method == "GET":
        return render_template('generate.html', user=current_user)

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        # Extract and validate required fields
        title = data.get("title")
        presenter = data.get("presenter")
        prompt = data.get("prompt")
        
        if not all([title, presenter, prompt]):
            return jsonify({"error": "Missing required fields: title, presenter, or prompt"}), 400

        # Extract optional fields with defaults
        num_slides = int(data.get("num_slides", 5))
        template_style = data.get("template_style", "Professional")

        # Initialize PPT generator
        ppt_generator = PPTGenerator()
        
        try:
            # Generate slide content
            slides_content = ppt_generator.generate_slide_content(prompt, num_slides)
            
            # Create presentation
            filepath = ppt_generator.create_presentation(
                title=title,
                presenter=presenter,
                slides_content=slides_content,
                template=template_style
            )
            
            # Get filename from path
            filename = os.path.basename(filepath)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'file_url': f'/download/{filename}'
            })
            
        except Exception as e:
            return jsonify({"error": f"Error generating presentation: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@bp.route("/download/<filename>")
@login_required
def download_file(filename):
    return send_from_directory(GENERATED_FOLDER, filename, as_attachment=True)


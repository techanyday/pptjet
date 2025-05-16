from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
        "web": {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "project_id": "pptjet",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["https://pptjet-dev.onrender.com/login/callback", "http://localhost:5000/login/callback"],
            "javascript_origins": ["https://pptjet-dev.onrender.com", "http://localhost:5000"]
        }
    }
    
    # Load OpenAI API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        print(f"Debug - API Key loaded: {api_key[:10]}...")
    else:
        print("WARNING: No OpenAI API key found!")
    
    # OAuth 2 client setup
    client = WebApplicationClient(client_secrets["web"]["client_id"])
    app.config['OAUTH_CLIENT'] = client
    
    # User session management setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    # Flask-Login helper to retrieve a user from our db
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Register blueprint with URL prefix
    from .routes import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/')
    
    # Add debug prints for template loading
    print(f"Template folder path: {app.template_folder}")
    print(f"Static folder path: {app.static_folder}")
    
    # Ensure the generated directory exists
    os.makedirs(os.path.join(os.path.dirname(app.root_path), 'generated'), exist_ok=True)
    
    return app

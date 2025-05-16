from flask_login import UserMixin
import json
import os

# Path to users data file
USERS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'users.json')

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    presentations_remaining = db.Column(db.Integer, default=3)  # Default for Free Plan

    @staticmethod
    def get(user_id):
        # Load users from JSON file
        users = load_users()
        if not user_id or user_id not in users:
            return None
        user = users[user_id]
        return User(
            id_=user["id"],
            name=user["name"],
            email=user["email"],
            profile_pic=user["profile_pic"],
            plan=user.get("plan", "free"),
            presentations=user.get("presentations", [])
        )

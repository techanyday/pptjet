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

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, plan='free', presentations=None):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.plan = plan
        self.presentations = presentations or []

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

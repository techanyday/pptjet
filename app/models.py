from flask_login import UserMixin

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
        # In a real application, you would fetch this from your database
        # For now, we'll use a simple in-memory storage
        from app import users_db
        if not user_id or user_id not in users_db:
            return None
        user = users_db[user_id]
        return User(
            id_=user["id"],
            name=user["name"],
            email=user["email"],
            profile_pic=user["profile_pic"],
            plan=user.get("plan", "free"),
            presentations=user.get("presentations", [])
        )

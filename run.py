import os
from dotenv import load_dotenv

from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure all database tables are created

        # Create a test user if none exists (example setup)
        from app.models import User
        if not User.query.first():
            test_user = User(username='test@example.com')
            test_user.set_password('test123')
            test_user.presentations_remaining = 3
            db.session.add(test_user)
            db.session.commit()
            print('Created test user: test@example.com / test123')

    app.run(debug=True)

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    email = "admin@example.com"
    password = "ChangeMe123!"

    existing = User.query.filter_by(email=email).first()
    if existing:
        print("Admin user already exists.")
    else:
        user = User(email=email, role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Admin user created.")
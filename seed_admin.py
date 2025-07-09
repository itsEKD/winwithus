import os
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from datetime import datetime
from app import create_app, mongo

# Load environment variables
load_dotenv()

# Create the Flask app
app = create_app()

# Create local bcrypt instance
bcrypt = Bcrypt(app)

# Define the admin user data
admin_user = {
    "username": "admin",
    "email": "admin@winwithus.com",
    "password": bcrypt.generate_password_hash("AdminPass123").decode('utf-8'),
    "is_admin": True,
    "is_confirmed": True,
    "created_at": datetime.utcnow(),
    "role": "admin",
    "tipster_status": "approved"
}

# Insert admin into MongoDB if it doesn't already exist
with app.app_context():
    if mongo.db.users.find_one({"email": admin_user["email"]}):
        print("⚠️  Admin user already exists.")
    else:
        mongo.db.users.insert_one(admin_user)
        print("✅ Admin user created successfully.")
print("MONGO_URI from env:", os.getenv("MONGO_URI"))

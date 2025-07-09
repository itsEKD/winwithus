# app/models/user.py

from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.username = user_doc.get('username')
        self.email = user_doc.get('email')
        self.is_admin = user_doc.get('is_admin', False)
        self.is_confirmed = user_doc.get('is_confirmed', False)
        self.role = user_doc.get('role', 'user')
        self.tipster_status = user_doc.get('tipster_status', 'pending')

    def get_id(self):
        return self.id

    def is_tipster(self):
        return self.tipster_status == 'approved'

    def is_system_admin(self):
        return self.is_admin or self.role == 'admin'

from app import mongo

# Example: read from a collection
users = mongo.db.users.find()

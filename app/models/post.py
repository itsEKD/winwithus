from datetime import datetime
from bson import ObjectId

class Post:
    def __init__(self, data):
        self.id = str(data.get('_id'))
        self.title = data.get('title')
        self.content = data.get('content')
        self.author = data.get('author')  # Can be username or user_id
        self.created_at = data.get('created_at', datetime.utcnow())

    def to_dict(self):
        return {
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at
        }

    def save(self, mongo):
        post_data = self.to_dict()
        post_data['created_at'] = datetime.utcnow()
        result = mongo.db.posts.insert_one(post_data)
        return str(result.inserted_id)

    @staticmethod
    def get_all(mongo):
        posts = mongo.db.posts.find().sort('created_at', -1)
        return [Post(post) for post in posts]

    @staticmethod
    def get_by_id(post_id, mongo):
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        return Post(post) if post else None

    @staticmethod
    def update(post_id, updates, mongo):
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {'$set': updates})

    @staticmethod
    def delete(post_id, mongo):
        mongo.db.posts.delete_one({'_id': ObjectId(post_id)})

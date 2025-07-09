from datetime import datetime
from bson import ObjectId


class Tip:
    def __init__(self, data):
        self.id = str(data.get('_id', ''))
        self.title = data.get('title', '')
        self.description = data.get('description', '')
        self.odds = data.get('odds', '')
        self.sport = data.get('sport', '')
        self.match_date = data.get('match_date')
        self.tipster_id = str(data.get('posted_by')) if data.get('posted_by') else ''
        self.tipster_name = data.get('tipster_name', '')
        self.created_at = data.get('created_at', datetime.utcnow())

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "odds": self.odds,
            "sport": self.sport,
            "match_date": self.match_date,
            "posted_by": ObjectId(self.tipster_id) if self.tipster_id else None,
            "tipster_name": self.tipster_name,
            "created_at": self.created_at
        }

    def save(self, mongo):
        result = mongo.db.tips.insert_one(self.to_dict())
        return str(result.inserted_id)

    @staticmethod
    def get_all(mongo):
        return [Tip(t) for t in mongo.db.tips.find().sort("created_at", -1)]

    @staticmethod
    def get_by_id(mongo, tip_id):
        tip = mongo.db.tips.find_one({"_id": ObjectId(tip_id)})
        return Tip(tip) if tip else None

    @staticmethod
    def update(mongo, tip_id, updates):
        mongo.db.tips.update_one({"_id": ObjectId(tip_id)}, {"$set": updates})

    @staticmethod
    def delete(mongo, tip_id):
        mongo.db.tips.delete_one({"_id": ObjectId(tip_id)})

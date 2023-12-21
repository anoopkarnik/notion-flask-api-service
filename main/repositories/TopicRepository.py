from main.models.AnkiModel import TopicModel as Topic
from extensions import db

class TopicRepository:
    def __init__(self):
        self.model = Topic

    def get_all(self):
        return self.model.query.all()
    
    def get_by_id(self, id):
        return self.model.query.get(id)
    
    def get_by_notion_page_id(self, notion_page_id):
        return self.model.query.filter_by(notion_page_id=notion_page_id).first()
    
    def get_by_deck_id(self, deck_id):
        return self.model.query.filter_by(deck_id=deck_id).first()
    
    def create_topic(self, created_at, updated_at, topic_name, notion_page_id, deck_id,deck_name):
        new_topic = self.model(
            created_at=created_at,
            updated_at=updated_at,
            topic_name=topic_name,
            notion_page_id=notion_page_id,
            deck_id=deck_id,
            deck_name=deck_name
        )
        db.session.add(new_topic)
        db.session.commit()
        return new_topic
    
    def delete_topic(self, id):
        topic = self.model.query.get(id)
        db.session.delete(topic)
        db.session.commit()
        return topic
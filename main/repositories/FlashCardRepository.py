from main.models.AnkiModel import FlashCardModel as FlashCard
from extensions import db

class FlashCardRepository:
    def __init__(self):
        self.model = FlashCard

    def get_all(self):
        return self.model.query.all()
    
    def get_by_id(self, id):
        return self.model.query.get(id)
    
    def get_by_deck_id(self, deck_id):
        return self.model.query.filter_by(deck_id=deck_id).all()
    
    def get_by_topic_id(self, topic_id):
        return self.model.query.filter_by(topic_id=topic_id).all()
    
    def create_flashcard(self, created_at, updated_at, notion_block_id, deck_id, front, topic_id,note_id):
        new_flash_card = self.model(
            created_at=created_at,
            updated_at=updated_at,
            notion_block_id=notion_block_id,
            deck_id=deck_id,
            front=front,
            topic_id=topic_id,
            note_id=note_id
        )
        db.session.add(new_flash_card)
        db.session.commit()
        return new_flash_card
    
    def update_flashcard(self, flash_card_id,updated_front,updated_back,updated_at):
        flash_card = self.model.query.get(flash_card_id)
        flash_card.updated_at = updated_at
        flash_card.front = updated_front
        flash_card.back = updated_back
        db.session.commit()
        return flash_card
    
    def delete_flash_card(self, id):
        flash_card = self.model.query.get(id)
        db.session.delete(flash_card)
        db.session.commit()
        return flash_card

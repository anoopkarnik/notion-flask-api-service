from extensions import db


class TopicModel(db.Model):
	__tablename__ = "topic"
	__table_args__ = {"schema":"notion_schema"}
	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.String(100))
	updated_at = db.Column(db.String(100))
	topic_name = db.Column(db.String(100))
	notion_page_id = db.Column(db.String(100))
	deck_id = db.Column(db.String(100))
	deck_name = db.Column(db.String(500))

	flash_cards = db.relationship('FlashCardModel', backref='topic', lazy=True)

	def __repr__(self):
		return f"Topic(id={self.id},topic_name={self.topic_name},notion_page_id={self.notion_page_id},deck_id={self.deck_id})"

class FlashCardModel(db.Model):
	__tablename__ = "flash_card"
	__table_args__ = {"schema":"notion_schema"}
	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.String(100))
	updated_at = db.Column(db.String(100))
	notion_block_id = db.Column(db.String(100))
	deck_id = db.Column(db.String(100))
	front = db.Column(db.String(500))
	topic_id = db.Column(db.Integer, db.ForeignKey('notion_schema.topic.id'))
	note_id = db.Column(db.String(100))

	def __repr__(self):
		return f"FlashCard(id={self.id},front={self.front},notion_block_id={self.notion_block_id},deck_id={self.deck_id},topic_id={self.topic_id}, note_id={self.note_id})"

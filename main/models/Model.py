from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Model(db.Model):
	__tablename__ = ""
	__table_args__ = {"schema":""}
	id = db.Column(db.Integer, primary_key=True)

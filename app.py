from flask import Flask
import threading
import os
# from main.models.Model import db
from main.controllers import Controller
from dotenv import load_dotenv
load_dotenv()

def create_app():
	app = Flask(__name__)
	# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+os.environ.get('DB_USERNAME')+':'+ os.environ.get('DB_PASSWORD')+'@'+ os.environ.get('DB_HOST')+':'+ os.environ.get('DB_PORT')+'/'+ os.environ.get('DB_NAME')
	# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	# db.init_app(app)
	# with app.app_context():
	# 	db.create_all()
	app.register_blueprint(Controller.payload_controller)
	return app

app = create_app()

if __name__ == "__main__":
	app.run(debug=True)
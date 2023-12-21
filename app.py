from flask import Flask
import threading
import os
import atexit
# from main.models.Model import db
from main.controllers import Controller,AnkiController,NotionController
from main.utils.scheduler import schedule_jobs
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import logging
from extensions import db

load_dotenv()

def create_app():
	app = Flask(__name__)
	logging.basicConfig(filename='logs/scheduler.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')
	app.logger.info('Info level log')
	app.logger.error('Error level log')
	app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	db.init_app(app)
	scheduler = BackgroundScheduler()
	schedule_jobs(scheduler)
	atexit.register(lambda: scheduler.shutdown())
	app.register_blueprint(Controller.payload_controller)
	app.register_blueprint(AnkiController.anki_controller)
	app.register_blueprint(NotionController.notion_controller)
	return app

app = create_app()

if __name__ == "__main__":
	with app.app_context():
		db.create_all()
	app.run(debug=True)
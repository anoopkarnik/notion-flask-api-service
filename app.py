from flask import Flask
import threading
import os
import atexit
# from main.models.Model import db
from main.controllers import Controller
from main.utils.scheduler import schedule_jobs
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import logging

load_dotenv()

def create_app():
	app = Flask(__name__)
	logging.basicConfig(filename='logs/scheduler.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')
	# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+os.environ.get('DB_USERNAME')+':'+ os.environ.get('DB_PASSWORD')+'@'+ os.environ.get('DB_HOST')+':'+ os.environ.get('DB_PORT')+'/'+ os.environ.get('DB_NAME')
	# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	# db.init_app(app)
	# with app.app_context():
	# 	db.create_all()
	app.logger.info('Info level log')
	app.logger.error('Error level log')
	scheduler = BackgroundScheduler()
	schedule_jobs(scheduler)
	atexit.register(lambda: scheduler.shutdown())
	app.register_blueprint(Controller.payload_controller)
	return app

app = create_app()

if __name__ == "__main__":
	app.run(debug=True)
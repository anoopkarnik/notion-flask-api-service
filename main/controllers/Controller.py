from flask import Blueprint, request, jsonify
from ..services.update_book_database import update_books
from ..services.update_movie_tvshow_database import update_new_movies_tvshows,update_existing_tvshows
from ..services.update_dashboard_status_database import create_dashboard_status_updates_page
from ..services.add_to_calendar import create_calendar_page
from ..services.notion_base_api import query_database,create_page,modify_page
from ..services.update_monthly_budget import get_financial_transaction_details
from ..services.voice_recording_to_notion_pages import transcribe_and_store
from ..services.youtube_playlist_to_notion_pages import store

payload_controller = Blueprint("payload_controller",__name__)

@payload_controller.route("/",methods=["GET"])
def health_check():
	return jsonify({"status":"success"})

@payload_controller.route("/database/<id>/query",methods=["POST"])
def query_database_controller(id):
	filters = request.json
	results = query_database(id,filters)
	return jsonify(results)

@payload_controller.route("/database/<id>",methods=["POST"])
def create_page_controller(id):
	properties = request.json
	results = create_page(id,properties)
	return jsonify({'results':results})

@payload_controller.route("/page/<id>",methods=["PATCH"])
def modify_page_controller(id):
	properties = request.json
	results = modify_page(id,properties)
	return jsonify({'results':results})

@payload_controller.route("/update_books",methods=["POST"])
def update_books_controller():
	update_books()
	return jsonify({'message':'Books updated'})

@payload_controller.route("/update_new_movies_tvshows",methods=["POST"])
def update_new_movies_tvshows_controller():
	update_new_movies_tvshows()
	return jsonify({'message':'Newly Created Movies and TV Shows updated'})


@payload_controller.route("/update_existing_tvshows",methods=["POST"])
def update_existing_tvshows_controller():
	update_existing_tvshows()
	return jsonify({'message':'Update Existing TV Shows updated'})


@payload_controller.route("/update_dashboard_status",methods=["POST"])
def update_dashboard_status_controller():
	create_dashboard_status_updates_page()
	return jsonify({'message':'Updated Dashboard Status Updates'})

@payload_controller.route("/add_to_calendar",methods=["POST"])
def create_calendar_controller():
	create_calendar_page()
	return jsonify({'message':'Created Calendar Pages Based on Schedule'})

@payload_controller.route("/update_monthly_budget",methods=["POST"])
def update_monthly_budget_controller():
	get_financial_transaction_details()
	return jsonify({'message':'Updated Monthly Budget'})

@payload_controller.route("/transcribe_voice_recording",methods=["POST"])
def transcribe_voice_recording_controller():
	data = request.json
	transcribe_and_store(data)
	return jsonify({'message':'Transcribed And Stored Voice Recording'})

@payload_controller.route("/transcribe_youtube_video",methods=["POST"])
def transcribe_youtube_video_controller():
	data = request.json
	store(data)
	return jsonify({'message':'Transcribed And Stored Youtube Video'})
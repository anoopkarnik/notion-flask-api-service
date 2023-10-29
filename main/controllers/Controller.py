from flask import Blueprint, request, jsonify
from ..services.update_book_database import update_books
from ..services.update_movie_tvshow_database import update_movies_tvshows
from ..services.update_dashboard_status_database import create_dashboard_status_updates_page

payload_controller = Blueprint("payload_controller",__name__)

@payload_controller.route("/",methods=["GET"])
def health_check():
	return jsonify({"status":"success"})

@payload_controller.route("/update_books",methods=["POST"])
def update_books_controller():
	update_books()
	return jsonify({'message':'Books updated'})

@payload_controller.route("/update_movies_tvshows",methods=["POST"])
def update_movies_tvshows_controller():
	update_movies_tvshows()
	return jsonify({'message':'Movies and TV Shows updated'})


@payload_controller.route("/update_dashboard_status",methods=["POST"])
def update_dashboard_status_controller():
	create_dashboard_status_updates_page()
	return jsonify({'message':'Updated Dashboard Status Updates'})
from flask import Blueprint, request, jsonify
from ..services.anki_connect import update_anki_decks

anki_controller = Blueprint("anki_controller",__name__)


@anki_controller.route("/update_anki_deck",methods=["POST"])
def update_anki_deck():
	update_anki_decks()
	return jsonify({'message':'Updated Anki Decks'})

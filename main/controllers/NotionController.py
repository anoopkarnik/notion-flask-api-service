from flask import Blueprint, request, jsonify
from ..services.notion_base_api import query_notion_database,create_notion_page,modify_notion_page,query_page_blocks,get_notion_page

notion_controller = Blueprint("notion_controller",__name__)

@notion_controller.route("/database/<id>/query",methods=["POST"])
def query_database_controller(id):
	body = request.json
	filters = body.get('filters',[])
	sorts = body.get('sorts',[])
	results = query_notion_database(id,filters,sorts)
	return jsonify(results)

@notion_controller.route("/database/<id>",methods=["POST"])
def create_page_controller(id):
	properties = request.json
	results = create_notion_page(id,properties)
	return jsonify({'results':results})

@notion_controller.route("/page/<id>",methods=["PATCH"])
def modify_page_controller(id):
	properties = request.json
	results = modify_notion_page(id,properties)
	return jsonify({'results':results})

@notion_controller.route("/block/<id>",methods=["GET"])
def get_page_block_controller(id):
	results = query_page_blocks(id,'parent')
	return jsonify({'results':results})


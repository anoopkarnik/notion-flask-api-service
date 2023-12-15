import os
import json
import datetime
import pytz
import requests
import time
from ..services.notion_base_api import query_notion_database,create_notion_page,modify_notion_page,query_page_blocks
import logging
from ..clients.anki_client import create_deck,get_all_cards,get_card_details,create_note

logger = logging.getLogger(__name__)


def update_anki_decks():
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_day_ago_gmt = current_time_gmt - datetime.timedelta(hours=24)
    areas_db_id = os.environ.get('AREAS_DB_ID')
    filters = []
    filters.append({'name':'Knowledge Type','type':'select','condition':'equals','value':'Self'})
    # filters.append({'type':'edited_time','condition':'on_or_after','value':one_day_ago_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    logger.info(f"Started querying database {areas_db_id} with filters {filters}")
    results = query_notion_database(areas_db_id,filters).get('results',[])
    for result in results:
        deck_created = result['Deck Created']
        id = result['id']
        # skill_type = result['Type']
        name = f"master::{result['Name']}"
        if not deck_created:
            deck_result = create_deck(name)
            deck_id = deck_result['result']
            logger.info(f"Created deck {name}")
            properties = []
            properties.append({'name':'Deck Created','type':'checkbox','condition':'equals','value':True})
            modify_notion_page(id,properties)
            logger.info(f"Updated Deck Created property for {name}")
        card_ids = get_all_cards(name)
        card_details = get_card_details(card_ids)
        # card_names = [x['fields']['Front']['value'] for x in card_details]
        logger.info(f"Got card details for {name}")
        blocks = query_page_blocks(id,'parent')
        logger.info(f"Blocks - {blocks}")
        for key,values in blocks.items():
            note_response = create_note(name,key,values)
            logger.info(note_response)
            logger.info(f"Created note for {key}")

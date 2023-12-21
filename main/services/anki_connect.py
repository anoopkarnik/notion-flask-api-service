import os
import json
import datetime
import pytz
import requests
import time
from ..services.notion_base_api import query_notion_database,create_notion_page,modify_notion_page,query_page_blocks,get_notion_page
import logging
from ..clients.anki_client import create_deck,get_all_cards,get_card_details,create_note
from ..repositories.TopicRepository import TopicRepository
from ..repositories.FlashCardRepository import FlashCardRepository

logger = logging.getLogger(__name__)
          
def update_anki_decks():
    skill_trees_db_id = os.environ.get('SKILL_TREES_DB_ID')
    filters = []
    filters.append({'name':'Parent-task','type':'relation','condition':'is_empty','value':True})
    results = query_notion_database(skill_trees_db_id,filters).get('results',[])
    for i,result in enumerate(results):
        deck_name=f"notes::{result['Type']}::{result['Skill Tree Name']}"
        create_deck(deck_name)
        create_notes_for_deck(deck_name,result['Self'])
        results[i]['Sub-tasks'] = get_subtask_data(result['Sub-tasks'],deck_name)
    return results

def get_subtask_data(subtasks,deck_name):
    for i,subtask in enumerate(subtasks):
        subtasks[i] = get_notion_page(subtask)
        new_deck_name= deck_name + f"::{subtasks[i]['Skill Tree Name']}"
        create_deck(new_deck_name)
        logger.info(f"Created deck {new_deck_name}")
        create_notes_for_deck(new_deck_name,subtasks[i]['Self'])
        if len(subtasks[i]['Sub-tasks'])>0: 
            subtasks[i]['Sub-tasks'] = get_subtask_data(subtasks[i]['Sub-tasks'],new_deck_name)
    return subtasks

def create_notes_for_deck(deck_name,note_page_ids):
    topic_repo = TopicRepository()
    flashcard_repo = FlashCardRepository()
    for note_page_id in note_page_ids:
        topic_row = topic_repo.get_by_notion_page_id(note_page_id)
        logger.info(f"Topic row - {topic_row}")
        if topic_row==None:
            note_page = get_notion_page(note_page_id)
            new_deck_name=deck_name+f"::{note_page['Name']}"
            deck_result = create_deck(new_deck_name)
            new_topic = topic_repo.create_topic(
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                topic_name=note_page['Name'],
                notion_page_id=note_page_id,
                deck_id=deck_result['result'],
                deck_name=new_deck_name
            )
            logger.info(f"Created topic {new_topic}")
            deck_id = deck_result['result']
            logger.info(f"Created deck {new_deck_name}")
            properties = []
            properties.append({'name':'Deck Created','type':'checkbox','condition':'equals','value':True})
            modify_notion_page(note_page_id,properties)
            logger.info(f"Updated Deck Created property for {new_deck_name}")
            card_ids = get_all_cards(new_deck_name)
            card_details = get_card_details(card_ids)
            # card_names = [x['fields']['Front']['value'] for x in card_details]
            logger.info(f"Got card details for {new_deck_name}")
            blocks = query_page_blocks(note_page_id,'parent')
            logger.info(f"Blocks - {blocks}")
            for key,value in blocks.items():
                note_response = create_note(new_deck_name,key,value['children'])
                logger.info(note_response)
                logger.info(f"Created note for {key}")
                new_flashcard = flashcard_repo.create_flashcard(
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                    notion_block_id=value['id'],
                    deck_id=deck_id,
                    front=key,
                    topic_id=new_topic.id,
                    note_id = note_response['result'][0]
                )
                logger.info(f"Created flashcard {new_flashcard}")

# Cases 
# 1) New self area is added 
# 2) New skill tree is added 
# 3) New flashcard added to self area 
# 4) Flashcard modified in self area
# 5) Self area transferred from one skill tree to another
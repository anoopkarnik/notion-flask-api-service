import os
import json
import datetime
import pytz
import requests
import time
import logging

logger = logging.getLogger(__name__)
url = os.environ.get('ANKI_CONNECT_URL')

def get_all_deck_details():
    pass

def get_deck_details():
    pass

def get_all_cards(name):
    payload = {
        "action": "findCards",
        "version": 6,
        "params": {
            "query": name
        }
    }
    response = requests.post(url,json=payload).json()
    return response['result']

def get_card_details(card_ids):
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": card_ids
        }
    }
    response = requests.post(url,json=payload).json()
    return response['result']

def create_deck(name):

    payload = {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": name
        }
    }
    response = requests.post(url,json=payload).json()
    return response

def delete_deck():
    pass

def create_note(deck_name,front,back):
    back_html = "<ol>"
    for item in back:
        back_html += f"<li>{item}</li>"
    back_html += "</ol>"
    payload = {
        "action": "addNotes",
        "version": 6,
        "params": {
            "notes": [{
                "deckName": deck_name,
                "modelName": "Basic",
                "fields": {
                    "Front": front,
                    "Back": back_html
                },
                "options": {
                    "allowDuplicate": False
                },
                "tags": [
                    "Notion Self Notes"
                ]
            }]
        }
    }
    logger.info(payload)
    response = requests.post(url,json=payload).json()
    return response

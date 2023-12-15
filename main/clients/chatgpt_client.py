import os
import json
import datetime
import pytz
import requests
import time
import logging

logger = logging.getLogger(__name__)

chatgpt_client_url = os.environ.get('CHATGPT_CLIENT_URL')
speech_to_text_context_path = os.environ.get('SPEECH_TO_TEXT_CONTEXT_PATH')
chat_context_path = os.environ.get('CHAT_CONTEXT_PATH')

def speech_to_text(location_path):
    speech_to_text_url = os.path.join(chatgpt_client_url,speech_to_text_context_path)
    payload = {'location_path':location_path}
    print(speech_to_text_url)
    print(payload)
    headers={'Content-Type':'application/json'}
    chatgpt_response = requests.post(speech_to_text_url, data=json.dumps(payload),headers=headers)
    logger.info(f"Response from chatgpt api - {chatgpt_response}")
    chatgpt_response=chatgpt_response.json()
    return chatgpt_response

def get_chatgpt_reply(system_instructions,format,message,model):
    chat_url = os.path.join(chatgpt_client_url,chat_context_path)
    payload = {'message':message,'system_instructions':system_instructions,'format':format,"model":model}
    chatgpt_response = requests.post(chat_url, data=json.dumps(payload),headers={'Content-Type':'application/json'})
    logger.info(f"Response from chatgpt api - {chatgpt_response}")
    chatgpt_response=chatgpt_response.json()
    return chatgpt_response
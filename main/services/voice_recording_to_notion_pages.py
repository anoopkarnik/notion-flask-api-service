import requests
import os
import json
from datetime import datetime
import pytz  # This library helps with time zone handling
import logging
import boto3
import requests
import pandas as pd
from ..services.notion_base_api import create_page,add_children_to_page

logger = logging.getLogger(__name__)

def transcribe_and_store(data):
    file_id = data['file_id']
    # Download the file from Google Drive
    logger.info(f"Downloading file {file_id}")
    response_stream = download_file_from_google_drive(file_id)
    # Upload the file to S3
    logger.info(f"Downloaded file {file_id}")
    s3_file_path = os.path.join(os.environ.get('VOICE_RECORDINGS_S3_FILE_PATH'),file_id+'.mp3')
    logger.info(f"Uploading file {file_id}")
    upload_to_s3(response_stream, s3_file_path)
    # # Transcribe the file
    logger.info(f"Uploading file {file_id}")
    logger.info(f"Transcribing file {file_id}")
    transcript = transcribe_file(s3_file_path)
    logger.info(f"Transcribed file {file_id}")
    logger.info(f"Getting details from transcript {file_id} through chatgpt")
    chatgpt_response = get_details_from_transcript(transcript)
    logger.info(f"this is the response = {chatgpt_response}")
    logger.info(f"Making paragraphs {file_id}")
    paragraphs = make_paragraphs(transcript,chatgpt_response)
    logger.info(f"Creating quick capture page {file_id}")
    notion_response = create_quick_capture_page(chatgpt_response,paragraphs)
    page_id = notion_response['id'].replace('-','')
    logger.info(f"Created quick capture page {file_id}")
    notion_response = modify_quick_capture_page(page_id,chatgpt_response,paragraphs)
    logger.info(f"Modified quick capture page {file_id}")
    return notion_response

def download_file_from_google_drive(file_id):
    URL = "https://drive.google.com/uc?id=" + file_id

    session = requests.Session()
    response = session.get(URL, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    return response

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def upload_to_s3(response_stream, s3_file_path):
    bucket_name = os.environ.get('VOICE_RECORDINGS_S3_BUCKET_NAME')
    s3 = boto3.client('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), 
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    s3.upload_fileobj(response_stream.raw, bucket_name, s3_file_path)

def transcribe_file(location_path):
    speech_to_text_url = os.path.join(os.environ.get('CHATGPT_CLIENT_URL'),os.environ.get('SPEECH_TO_TEXT_CONTEXT_PATH'))
    payload = {'location_path':location_path}
    print(speech_to_text_url)
    print(payload)
    response = requests.post(speech_to_text_url, data=json.dumps(payload),headers={'Content-Type':'application/json'}).json()
    return response['text']

def get_details_from_transcript(transcript):
    chat_url = os.path.join(os.environ.get('CHATGPT_CLIENT_URL'),os.environ.get('CHAT_CONTEXT_PATH'))
    system_instructions = """You are an assistant with expertise PHD in psychology and philosophy in all fields and speak only JSON. 
    Do not write normal txt. Example formatting: {"title":"A string" , "summary": "A String", "main_points": ["A String","A String"],
    "action_items": {"tasks":["A String","A String"],"habits":["A String","A String"]},"follow_up": ["A String","A String"],"arguments": ["A String","A String"]}"""
    format = "json_object"
    message = """Analyze the transcript provided below and then provde the following : title,summary (in transcript size by
    10),main_points (covering all important things),
     action_items (covering all actions possible as a task and or as habits),follow_up( Follow up questions which need to be 
    researched on), get_arguments (arguments against the transcript) ---"""+transcript  
    payload = {'message':message,'system_instructions':system_instructions,'format':format}
    chatgpt_response = requests.post(chat_url, data=json.dumps(payload),headers={'Content-Type':'application/json'}).json()
    return chatgpt_response
    
def make_paragraphs(transcript,response):
    summary = json.loads(response['choices'][0]['message']['content'])['summary']
    transcriptWords = transcript.split(' ')
    summaryWords = summary.split(' ')
    wordsPerParagraph = 100

    def sentenceGrouper(arr):
        newArray = []
        for i in range(0,len(arr),wordsPerParagraph):
            group = []
            for j in range(i,i+wordsPerParagraph):
                if j<len(arr):
                    group.append(arr[j])
            newArray.append(' '.join(group))
        return newArray
    
    paragraphs = sentenceGrouper(transcriptWords)
    summaryParagraphs = sentenceGrouper(summaryWords)

    allParagraphs = {        
        'transcript':paragraphs,
        'summary':summaryParagraphs
    }
    # Return data for use in future steps
    return allParagraphs

def create_quick_capture_page(response,paragraphs):
    gptTurboRate = 0.001
    tokens = response['usage']['total_tokens']
    chat_cost = round((float(tokens)*gptTurboRate),3)
    title = json.loads(response['choices'][0]['message']['content'])['title']
    logger.info("Started Creating Page")
    properties = []
    properties.append({'name':'Name','type':'title','value':title})
    properties.append({'name':'Tags','type':'select','value':'Voice Notes'})
    properties.append({'name':'AI Cost','type':'number','value':chat_cost})
    response = create_page(os.environ.get('QUICK_CAPTURE_DB_ID'),properties)
    logger.info("Created Page")
    return response

def modify_quick_capture_page(page_id,chatgpt_response,paragraphs):
    logger.info(f"Updating Page {page_id}")
    date = datetime.today().strftime('%Y-%m-%d')
    children = []
    children.append({'type':'callout','value':{
        'rich_text':[
            {"text":{"content": " This AI transcription and summary was created on "}},
            {"mention" : {"type" : "date" , "date": {"start":date}}},
            {"text":{"content":". "}}
        ],"color":"blue_background"}})
    children.append({'type':'table_of_contents','value':{'color':'default'}})
    children.append({'type':'heading_1','value':{'rich_text':[{'text':{'content':'Summary'}}]}})
    for summary in paragraphs['summary']:
        children.append({'type':'paragraph','value':{'rich_text':[{"text":{"content":summary}}]}})
    content = json.loads(chatgpt_response['choices'][0]['message']['content'])
    children.append({'type':'heading_1','value':{'rich_text':[{'text':{'content':'Main Points'}}]}})
    for item in content['main_points']:
        children.append({'type':'bulleted_list_item','value':{'rich_text':[{'text':{'content':item}}]}})
    children.append({'type':'heading_1','value':{'rich_text':[{'text':{'content':'Potential Action Items'}}]}})
    children.append({'type':'heading_2','value':{'rich_text':[{'text':{'content':'Potential Tasks'}}]}})
    for item in content['action_items']['tasks']:
        children.append({'type':'to_do','value':{'rich_text':[{'text':{'content':item}}]}})
    children.append({'type':'heading_2','value':{'rich_text':[{'text':{'content':'Potential Habits'}}]}}) 
    for item in content['action_items']['habits']:
        children.append({'type':'to_do','value':{'rich_text':[{'text':{'content':item}}]}})
    children.append({'type':'heading_1','value':{'rich_text':[{'text':{'content':'Follow Up Questions'}}]}})
    for item in content['follow_up']:
        children.append({'type':'bulleted_list_item','value':{'rich_text':[{'text':{'content':item}}]}})
    children.append({'type':'heading_1','value':{'rich_text':[{'text':{'content':'Arguments against the thoughts'}}]}})
    for item in content['arguments']:
        children.append({'type':'bulleted_list_item','value':{'rich_text':[{'text':{'content':item}}]}})
    children.append({'type':'heading_1','value':{'rich_text':[{'text':{'content':'Transcript'}}]}}) 
    for transcript in paragraphs['transcript']:
        children.append({'type':'paragraph','value':{'rich_text':[{"text":{"content":transcript}}]}})
    response = add_children_to_page(page_id,children)
    logger.info("Updated Page")
    return response

# FILE_ID = '1iszqu-2WdfLhsy6L8Ww6ec5cytZOZj2h'
# BUCKET_NAME = 'chatgpt-audio'
# S3_FILE_NAME = 'voice-recordings/'+FILE_ID+'.mp3'

# response_stream = download_file_from_google_drive(FILE_ID)
# upload_to_s3(response_stream, BUCKET_NAME, S3_FILE_NAME)


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
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)

def store(data):
    video_id = data['video_id']
    # Download the file from Google Drive
    transcript = get_transcript_from_video(video_id)
    chatgpt_response = get_details_from_transcript(transcript)
    logger.info(f"this is the response = {chatgpt_response}")
    paragraphs = make_paragraphs(transcript,chatgpt_response)
    notion_response = create_quick_capture_page(chatgpt_response,paragraphs,video_id)
    page_id = notion_response['id'].replace('-','')
    notion_response = modify_quick_capture_page(page_id,chatgpt_response,paragraphs,video_id)
    return notion_response


def get_transcript_from_video(video_id):
    dicts = YouTubeTranscriptApi.get_transcript(video_id)
    text = ' '.join([x['text'] for x in dicts])
    return text

def get_details_from_transcript(transcript):
    chat_url = os.path.join(os.environ.get('CHATGPT_CLIENT_URL'),os.environ.get('CHAT_CONTEXT_PATH'))
    system_instructions = """You are an assistant with expertise PHD in psychology and philosophy in all fields and speak only JSON. 
    Do not write normal txt. Example formatting: {"title":"A string" , "summary": "A String", "main_points": ["A String","A String"],
    "action_items": {"tasks":["A String","A String"],"habits":["A String","A String"]},"follow_up": ["A String","A String"],"arguments": ["A String","A String"]},"stories":["A String","A String"]"""
    format = "json_object"
    message = """Analyze the transcript provided below and then provde the following : title,summary (in transcript size by
    10),main_points (covering all important things in bulleted lists),
     action_items (covering all actions possible as a task and or as habits in to_do lists),follow_up( Follow up questions which need to be 
    researched on in bulleted lists), get_arguments (arguments against the transcript in bulletted lists), stories (stories in the transcript in bulletted lists) ---"""+transcript  
    payload = {'message':message,'system_instructions':system_instructions,'format':format,"model":"gpt-3.5-turbo-1106"}
    chatgpt_response = requests.post(chat_url, data=json.dumps(payload),headers={'Content-Type':'application/json'})
    logger.info(f"Response from chatgpt api - {chatgpt_response}")
    chatgpt_response=chatgpt_response.json()
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

def create_quick_capture_page(response,paragraphs,video_id):
    gptTurboRate = 0.001
    tokens = response['usage']['total_tokens']
    chat_cost = round((float(tokens)*gptTurboRate)/1000,3)
    title = json.loads(response['choices'][0]['message']['content'])['title']
    logger.info("Started Creating Page")
    properties = []
    properties.append({'name':'Name','type':'title','value':title})
    properties.append({'name':'Tags','type':'select','value':'AI Youtube Transcription'})
    properties.append({'name':'AI Cost','type':'number','value':chat_cost})
    properties.append({'name':'URL','type':'url','value':f"https://www.youtube.com/watch?v={str(video_id)}"})
    response = create_page(os.environ.get('QUICK_CAPTURE_DB_ID'),properties)
    logger.info("Created Page")
    return response

def modify_quick_capture_page(page_id,chatgpt_response,paragraphs,video_id):
    logger.info(f"Updating Page {page_id}")
    date = datetime.today().strftime('%Y-%m-%d')
    children = []
    children.append({'type':'embed', 'value':{
        'url':f"https://www.youtube.com/watch?v={str(video_id)}",
        }})
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
    children.append({'type':'heading_1','value':{'rich_text':[{'text':{'content':'Stories'}}]}})
    for item in content['stories']:
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


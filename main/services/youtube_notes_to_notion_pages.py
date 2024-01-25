import requests
import os
import json
from datetime import datetime
import pytz  # This library helps with time zone handling
import logging
import boto3
import requests
import pandas as pd
from ..services.notion_base_api import create_notion_page,add_children_to_page
from youtube_transcript_api import YouTubeTranscriptApi
from ..clients.chatgpt_client import speech_to_text,get_chatgpt_reply
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

def store_youtube_videos(data):
    video_id = data['video_id']
    playlist_type = data.get('playlist_type','')
    video_details = get_video_details(video_id)
    logger.info(f"Got video details from video")
    video_page_response = create_video_page(video_id,video_details)
    logger.info(f"Created Video Page")
    if playlist_type == 'Note Taking':
        transcript = get_transcript_from_video(video_id)
        logger.info("Got transcript from video")
        chatgpt_response = get_details_from_transcript(transcript)
        logger.info(f"this is the response = {chatgpt_response}")
        paragraphs = make_paragraphs(transcript,chatgpt_response)
        logger.info(f"Made paragraphs")
        notion_response = create_areas_page(chatgpt_response,paragraphs,video_id,video_details['title'],video_page_response)
        logger.info(f"Created page")
        page_id = notion_response['id'].replace('-','')
        notion_response = modify_areas_page(page_id,chatgpt_response,paragraphs,video_id)
        logger.info(f"Modified page")
        return notion_response
    else:
        return video_page_response

def get_video_details(video_id):
    youtube = build('youtube', 'v3', developerKey=os.environ.get('YOUTUBE_API_KEY'))
    result = {}
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    if response['items']:
        result['title'] = response['items'][0]['snippet']['title']
        result['channelTitle'] = response['items'][0]['snippet'].get('channelTitle','')
        result['language'] = response['items'][0]['snippet'].get('defaultAudioLanguage','')
        result['description'] = response['items'][0]['snippet'].get('description','')
        result['channelId'] = response['items'][0]['snippet'].get('channelId','')
        result['tags'] = response['items'][0]['snippet'].get('tags',[])
    
    request = youtube.videos().list(
        part="statistics",
        id=video_id
    )
    response = request.execute()
    if response['items']:
        result['views'] = int(response['items'][0]['statistics'].get('viewCount',0))
        result['likes'] = int(response['items'][0]['statistics'].get('likeCount',0))
        result['dislikes'] = int(response['items'][0]['statistics'].get('dislikeCount',0))
        result['comments'] = int(response['items'][0]['statistics'].get('commentCount',0))
    return result


def create_video_page(video_id,video_details):
    logger.info("Started Creating Page")
    properties = []
    properties.append({'name':'Name','type':'title','value':video_details['title']})
    properties.append({'name':'Platform','type':'select','value':'Youtube'})
    properties.append({'name':'Language','type':'select','value':video_details['language']})
    properties.append({'name':'URL','type':'url','value':f"https://www.youtube.com/watch?v={str(video_id)}"})
    properties.append({'name':'Channel','type':'select','value':video_details['channelTitle']})
    properties.append({'name':'ChannelID','type':'select','value':video_details['channelId']})
    properties.append({'name':'Tags','type':'multi_select','value':video_details['tags']})
    properties.append({'name':'views','type':'number','value':video_details['views']})
    properties.append({'name':'likes','type':'number','value':video_details['likes']})
    properties.append({'name':'dislikes','type':'number','value':video_details['dislikes']})
    properties.append({'name':'comments','type':'number','value':video_details['comments']})
    response = create_notion_page(os.environ.get('VIDEOS_DB_ID'),properties)
    logger.info("Created Page")
    children = []
    children.append({'type':'embed', 'value':f"https://www.youtube.com/watch?v={str(video_id)}"})
    children.append({'type':'heading_1','value':'Description'})
    lines = video_details['description'].split('\n')
    for line in lines:
        children.append({'type':'paragraph','value':line})
    child_response = add_children_to_page(response['id'],children)
    logger.info(f"Updated Page with blocks :{child_response}")
    return response


def get_transcript_from_video(video_id):
    dicts = YouTubeTranscriptApi.get_transcript(video_id)
    text = ' '.join([x['text'] for x in dicts])
    return text

def get_details_from_transcript(transcript):
    system_instructions = """You are an assistant with expertise PHD in psychology and philosophy in all fields and speak only JSON. 
    Do not write normal txt. Example formatting: {"summary": "A String", "main_points": ["A String","A String"],
    "action_items": {"tasks":["A String","A String"],"habits":["A String","A String"]},"follow_up": ["A String","A String"],"arguments": ["A String","A String"]},"stories":["A String","A String"]"""
    format = "json_object"
    message = """Analyze the transcript provided below and then provde the following : summary (size of the summary should be around number of words in transcript / 10),main_points (covering all important things in bulleted lists),
     action_items (covering all actions possible as a task and or as habits in to_do lists),follow_up( All Possible Follow up questions which need to be 
    researched on in bulleted lists), get_arguments (all possible arguments against the transcript in bulletted lists), stories (all possible stories in the transcript in bulletted lists) ---"""+transcript  
    chatgpt_response = get_chatgpt_reply(system_instructions,format,message,"gpt-4-1106-preview")
    logger.info(f"Response from chatgpt api - {chatgpt_response}")
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

def create_areas_page(response,paragraphs,video_id,title,video_page_response):
    gptTurboRate = 0.001
    tokens = response['usage']['total_tokens']
    chat_cost = round((float(tokens)*gptTurboRate)/1000,3)
    logger.info("Started Creating Page")
    properties = []
    properties.append({'name':'Name','type':'title','value':title})
    properties.append({'name':'Tags','type':'select','value':'AI Youtube Transcription'})
    properties.append({'name':'AI Cost','type':'number','value':chat_cost})
    properties.append({'name':'URL','type':'url','value':f"https://www.youtube.com/watch?v={str(video_id)}"})
    properties.append({'name':'Videos','type':'relation','value':[video_page_response['id']]})
    response = create_notion_page(os.environ.get('AREAS_DB_ID'),properties)
    logger.info("Created Page")
    return response

def modify_areas_page(page_id,chatgpt_response,paragraphs,video_id):
    logger.info(f"Updating Page {page_id}")
    date = datetime.today().strftime('%Y-%m-%d')
    children = []
    children.append({'type':'embed', 'value':f"https://www.youtube.com/watch?v={str(video_id)}"})
    children.append({'type':'callout','value':{
        'rich_text':[
            {"text":{"content": " This AI transcription and summary was created on "}},
            {"mention" : {"type" : "date" , "date": {"start":date}}},
            {"text":{"content":". "}}
        ],"color":"blue_background"}})
    children.append({'type':'table_of_contents'})
    children.append({'type':'heading_1','value':'Summary'})
    for summary in paragraphs['summary']:
        children.append({'type':'paragraph','value':summary})
    content = json.loads(chatgpt_response['choices'][0]['message']['content'])
    children.append({'type':'heading_1','value':'Main Points'})
    for item in content['main_points']:
        children.append({'type':'bulleted_list_item','value':item})
    children.append({'type':'heading_1','value':'Potential Action Items'})
    children.append({'type':'heading_2','value':'Potential Tasks'})
    for item in content['action_items'].get('tasks',[]):
        children.append({'type':'to_do','value':item})
    children.append({'type':'heading_2','value':'Potential Habits'}) 
    for item in content['action_items'].get('habits',[]):
        children.append({'type':'to_do','value':item})
    children.append({'type':'heading_1','value':'Follow Up Questions'})
    for item in content.get('follow_up',[]):
        children.append({'type':'bulleted_list_item','value':item})
    children.append({'type':'heading_1','value':'Arguments against the thoughts'})
    for item in content.get('arguments',[]):
        children.append({'type':'bulleted_list_item','value':item})
    children.append({'type':'heading_1','value':'Stories'})
    for item in content.get('stories',[]):
        children.append({'type':'bulleted_list_item','value':item})
    children.append({'type':'heading_1','value':'Transcript'}) 
    for transcript in paragraphs['transcript']:
        children.append({'type':'paragraph','value':transcript})
    for i in range(0,len(children),100):
        response = add_children_to_page(page_id,children[i:i+100])
        logger.info(f"Updated Page with blocks :{response}")
    return response

# FILE_ID = '1iszqu-2WdfLhsy6L8Ww6ec5cytZOZj2h'
# BUCKET_NAME = 'chatgpt-audio'
# S3_FILE_NAME = 'voice-recordings/'+FILE_ID+'.mp3'

# response_stream = download_file_from_google_drive(FILE_ID)
# upload_to_s3(response_stream, BUCKET_NAME, S3_FILE_NAME)


import requests
import os
import json
import datetime
import pytz  # This library helps with time zone handling

def update_books():
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    ten_minutes_ago_gmt = current_time_gmt - datetime.timedelta(minutes=10)
    notion_url = os.environ.get('NOTION_URL')
    notion_database_url = os.path.join(notion_url,'databases')
    book_database_id = os.environ.get('BOOKS_DB_ID')
    notion_book_database_url = os.path.join(notion_database_url,book_database_id,"query")
    token = os.environ.get('NOTION_TOKEN')
    # data = json.dumps({
    #     "filter": {
    #         "property": "Summary",
    #         "rich_text": {
    #             "is_empty": True
    #         }
    #     }
    # })
    data = json.dumps({
        "filter": {
            "timestamp": "last_edited_time",
            "last_edited_time": {
                "on_or_after": ten_minutes_ago_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }
    })
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    response = requests.post(notion_book_database_url,headers=headers,data=data).json()
    for result in response['results']:
        id = result['id']
        title = result['properties']['Name']['title'][0]['plain_text']
        
        book_details = get_google_books_details(title)
        print(f"Started Updating properties for {title}")
        update_book_properties(id,book_details)
        print(f"Completed Updating properties for {title}")


def get_google_books_details(title):
    google_books_url = os.environ.get('GOOGLE_BOOKS_URL')
    params = {}
    params['q']=title
    params['startIndex']=0
    params['maxResults']=1
    response = requests.get(google_books_url,params=params).json()
    return response['items'][0]['volumeInfo']
    


def update_book_properties(id,book_details):
    notion_url = os.environ.get('NOTION_URL')
    notion_page_url = os.path.join(notion_url,'pages',id)
    token = os.environ.get('NOTION_TOKEN')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    properties = {}
    if 'authors' in book_details:
        properties['Author'] = {"rich_text":[{"text":{"content":','.join(book_details['authors'])}}]}
    properties['Summary'] = {"rich_text":[{"text":{"content":book_details.get('description','')}}]}
    properties['Subtitle'] = {"rich_text":[{"text":{"content":book_details.get('subtitle','')}}]}
    properties['Published Date'] = {"date":{"start":book_details.get('publishedDate','')}}
    properties['Page Count'] = {"number":book_details.get('pageCount','')}
    if 'imageLinks' in book_details:
        properties['Thumbnail'] = {"files":[{"type":"external","name":"Book Cover","external":{"url":book_details['imageLinks']['thumbnail']}}]}
    if 'categories' in book_details:
        properties['Genres'] = {}
        properties['Genres']['multi_select'] = []
        for category in book_details['categories']:
            properties['Genres']['multi_select'].append({'name':category})
    body = json.dumps({'properties':properties})
    response = requests.request('PATCH',notion_page_url,headers=headers,data=body)
    



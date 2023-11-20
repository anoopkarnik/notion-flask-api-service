import requests
import os
import json
import datetime
import pytz  # This library helps with time zone handling
from ..services.notion_base_api import query_database,create_page,modify_page
import logging

logger = logging.getLogger(__name__)


def update_books():
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    ten_minutes_ago_gmt = current_time_gmt - datetime.timedelta(minutes=5)
    book_database_id = os.environ.get('BOOKS_DB_ID')
    filters = []
    filters.append({'type':'last_edited_time','condition':'on_or_after','value':ten_minutes_ago_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    results = query_database(book_database_id,filters).get('results',[])
    for result in results:
        id = result['id']
        title = result['Name']
        book_details = get_google_books_details(title)
        logger.info(f"Started Updating properties for {title}")
        update_book_properties(id,book_details)
        logger.info(f"Completed Updating properties for {title}")


def get_google_books_details(title):
    google_books_url = os.environ.get('GOOGLE_BOOKS_URL')
    params = {}
    params['q']=title
    params['startIndex']=0
    params['maxResults']=1
    response = requests.get(google_books_url,params=params).json()
    return response['items'][0]['volumeInfo']
    
def update_book_properties(id,book_details):
    properties = []
    if 'authors' in book_details:
        properties.append({'name':'Author','type':'text','value':','.join(book_details['authors'])})
    properties.append({'name':'Summary','type':'text','value':book_details.get('description','')})
    properties.append({'name':'Subtitle','type':'text','value':book_details.get('subtitle','')})
    properties.append({'name':'Published Date','type':'date','value':book_details.get('publishedDate','')})
    properties.append({'name':'Page Count','type':'number','value':book_details.get('pageCount','')})
    if 'imageLinks' in book_details:
        properties.append({'name':'Thumbnail','type':'file_url','value':book_details['imageLinks']['thumbnail']})
    if 'categories' in book_details:
        properties.append({'name':'Genres','type':'multi_select','value':[x for x in book_details['categories']]})
    response = modify_page(id,properties)
    



import os
import json
import requests

google_books_url = os.environ.get('GOOGLE_BOOKS_URL')

def get_google_books_details(title):
    params = {}
    params['q']=title
    params['startIndex']=0
    params['maxResults']=1
    response = requests.get(google_books_url,params=params).json()
    return response['items'][0]['volumeInfo']
import os
import json
import datetime
import pytz
import requests
import time
import logging

logger = logging.getLogger(__name__)

tmdb_movie_query_url = os.environ.get('TMDB_MOVIE_QUERY_URL')
tmdb_tvshow_query_url = os.environ.get('TMDB_TVSHOW_QUERY_URL')
tmdb_movie_id_url = os.environ.get('TMDB_MOVIE_ID_URL')
tmdb_tvshow_id_url = os.environ.get('TMDB_TVSHOW_ID_URL')
token = os.environ.get('TMDB_TOKEN')

def search_by_title(title,type):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {}
    params['query']=title
    if type == 'Film':
        query_url = tmdb_movie_query_url
    else:
        query_url = tmdb_tvshow_query_url
    response = requests.get(query_url,headers=headers,params=params).json()
    return response

def search_by_id(type,id):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    if type == 'Film':
        id_url = tmdb_movie_id_url
    else:
        id_url = tmdb_tvshow_id_url
    id_url +=f'/{id}'
    response_details = requests.get(id_url,headers=headers).json()
    return response_details
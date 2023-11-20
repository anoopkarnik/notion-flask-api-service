import requests
import os
import json
import datetime
import pytz
import time  # This library helps with time zone handling
from ..services.notion_base_api import query_database,create_page,modify_page
import logging

logger = logging.getLogger(__name__)

def update_movies_tvshows():
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    ten_minutes_ago_gmt = current_time_gmt - datetime.timedelta(minutes=2)
    database_id = os.environ.get('MOVIE_TVSHOW_DB_ID')
    token = os.environ.get('NOTION_TOKEN')
    filters = []
    # filters.append({'name':'Original Language','type':'select','condition':'is_empty','value':True})
    filters.append({'type':'created_time','condition':'on_or_after','value':ten_minutes_ago_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    results = query_database(database_id,filters).get('results',[])
    for result in results:
        id = result['id']
        title = result['Name']
        type = result['Type']
        movie_tvshow_details = get_tmdb_movies_tvshows_details(title,type)
        if movie_tvshow_details:
            logger.info(f"Started Updating properties for {title}")
            update_movie_tvshow_properties(id,type,movie_tvshow_details)
            logger.info(f"Completed Updating properties for {title}")


def get_tmdb_movies_tvshows_details(title,type):
    tmdb_movie_query_url = os.environ.get('TMDB_MOVIE_QUERY_URL')
    tmdb_tvshow_query_url = os.environ.get('TMDB_TVSHOW_QUERY_URL')
    tmdb_movie_id_url = os.environ.get('TMDB_MOVIE_ID_URL')
    tmdb_tvshow_id_url = os.environ.get('TMDB_TVSHOW_ID_URL')
    token = os.environ.get('TMDB_TOKEN')
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {}
    params['query']=title
    if type == 'Film':
        query_url = tmdb_movie_query_url
        id_url = tmdb_movie_id_url
    else:
        query_url = tmdb_tvshow_query_url
        id_url = tmdb_tvshow_id_url
    response = requests.get(query_url,headers=headers,params=params).json()
    if len(response['results'])>0:
        id = response['results'][0]['id']
        id_url +=f'/{id}'
        response_details = requests.get(id_url,headers=headers).json()
        return response_details
    else:
        return False
    


def update_movie_tvshow_properties(id,type,movie_tvshow_details):
    tmdb_image_url = os.environ.get('TMDB_IMAGE_URL')
    properties = []
    properties.append({'name':'overview','type':'text','value':movie_tvshow_details.get('overview','')})
    properties.append({'name':'rating_average','type':'number','value':movie_tvshow_details.get('vote_average','')})
    if movie_tvshow_details['poster_path']:
        properties.append({'name':'poster','type':'file_url','value':tmdb_image_url+movie_tvshow_details.get('poster_path')})
    if 'genres' in movie_tvshow_details:
        properties.append({'name':'Genre','type':'multi_select','value':[x['name'] for x in movie_tvshow_details['genres']]})
    properties.append({'name':'Original Language','type':'select','value':movie_tvshow_details.get('original_language','')})
    properties.append({'name':'Available Languages','type':'multi_select','value':movie_tvshow_details.get('languages',[])})
    if type == 'Film':
        properties.append({'name':'release_date','type':'date','value':movie_tvshow_details.get('release_date','')})
    else:
        properties.append({'name':'release_date','type':'date','value':movie_tvshow_details.get('first_air_date','')})
        properties.append({'name':'Total Episodes','type':'number','value':movie_tvshow_details.get('number_of_episodes','')})
        properties.append({'name':'Total Seasons','type':'number','value':movie_tvshow_details.get('number_of_seasons','')})
        properties.append({'name':'status','type':'select','value':movie_tvshow_details.get('status','')})
        if movie_tvshow_details['next_episode_to_air'] != None:
            properties.append({'name':'Next Episode Date','type':'date','value': movie_tvshow_details['next_episode_to_air'].get('air_date','')})
        seasons = movie_tvshow_details['seasons']
        season_episodes = ""
        season_details = ""
        for season in seasons:
            season_episodes +=season.get('name')
            season_episodes += " - "
            season_episodes += str(season.get('episode_count',''))
            season_episodes +=" | "
            season_details += season.get('name')
            season_details += " - "
            season_details += season.get('overview')
            season_details += " | "
        properties.append({'name':'Season Episodes','type':'text','value':season_episodes})
        properties.append({'name':'Season Details','type':'text','value':season_details[:2000]})
    response = modify_page(id,properties)
    logger.info(response)
import requests
import os
import json
import datetime
import pytz
import time  # This library helps with time zone handling
from ..services.notion_base_api import query_notion_database,create_notion_page,modify_notion_page,add_children_to_page,delete_page_blocks
import logging
from ..clients.tmdb_client import search_by_id,search_by_title

logger = logging.getLogger(__name__)

def get_time(type,number):
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    if type == 'daily':
        past_time = current_time_gmt - datetime.timedelta(days=number)
        return past_time.strftime("%Y-%m-%dT%H:%M:%SZ") 
    elif type == 'weekly':
        past_time = current_time_gmt - datetime.timedelta(weeks=number)
        return past_time.strftime("%Y-%m-%dT%H:%M:%SZ") 
    elif type == 'monthly':
        past_time = current_time_gmt - datetime.timedelta(months=number)
        return past_time.strftime("%Y-%m-%dT%H:%M:%SZ") 
    elif type == 'minutes':
        past_time = current_time_gmt - datetime.timedelta(minutes=number)
        return past_time.strftime("%Y-%m-%dT%H:%M:%SZ") 
    elif type == 'hours':
        past_time = current_time_gmt - datetime.timedelta(hours=number)
        return past_time.strftime("%Y-%m-%dT%H:%M:%SZ") 
    else:
        return None

def update_new_movies_tvshows():
    past_time_string = get_time('minutes',10)
    database_id = os.environ.get('MOVIE_TVSHOW_DB_ID')
    filters = []
    # filters.append({'name':'Original Language','type':'select','condition':'is_empty','value':True})
    filters.append({'type':'created_time','condition':'on_or_after','value':past_time_string})
    # filters.append({'name':'Type','type':'select','condition':'equals','value':'TV Series'})
    results = query_notion_database(database_id,filters).get('results',[])
    loop_through_results(results)

def update_existing_tvshows():
    database_id = os.environ.get('MOVIE_TVSHOW_DB_ID')
    filters = []
    # filters.append({'name':'Original Language','type':'select','condition':'is_empty','value':True})
    filters.append({'name':'Type','type':'select','condition':'equals','value':'TV Series'})
    filters.append({'name':'status','type':'select','condition':'equals','value':'Returning Series'})
    results = query_notion_database(database_id,filters).get('results',[])
    loop_through_results(results)

def loop_through_results(results):
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
    response = search_by_title(title,type)
    if len(response['results'])>0:
        id = response['results'][0]['id']
        response_details = search_by_id(type,id)
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
        children = []
        for season in seasons:
            children.append({'type':'heading_3','value':season.get('name') +' - ' + str(season.get('episode_count',''))})
            children.append({'type':'paragraph','value':season.get('overview')})
    response = modify_notion_page(id,properties)
    logger.info(response)
    response = delete_page_blocks(id)
    logger.info(response)
    response = add_children_to_page(id,children)
    logger.info(response)


    
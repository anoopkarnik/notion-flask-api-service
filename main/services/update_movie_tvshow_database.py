import requests
import os
import json
import datetime
import pytz  # This library helps with time zone handling

def update_movies_tvshows():
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    ten_minutes_ago_gmt = current_time_gmt - datetime.timedelta(minutes=10)
    notion_url = os.environ.get('NOTION_URL')
    notion_database_url = os.path.join(notion_url,'databases')
    movie_tvshow_database_id = os.environ.get('MOVIE_TVSHOW_DB_ID')
    notion_movie_tvshow_database_url = os.path.join(notion_database_url,movie_tvshow_database_id,"query")
    token = os.environ.get('NOTION_TOKEN')
    data = json.dumps({
        "filter": {
            "property": "overview",
            "rich_text": {
                "is_empty": True
            }
        }
    })
    # data = json.dumps({
    #     "filter": {
    #         "timestamp": "last_edited_time",
    #         "last_edited_time": {
    #             "on_or_after": ten_minutes_ago_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    #         }
    #     }
    # })
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    response = requests.post(notion_movie_tvshow_database_url,headers=headers,data=data).json()
    for result in response['results']:
        id = result['id']
        title = result['properties']['Name']['title'][0]['plain_text']
        type = result['properties']['Type']['select']['name']
        movie_tvshow_details = get_tmdb_movies_tvshows_details(title,type)
        if movie_tvshow_details:
            print(f"Started Updating properties for {title}")
            update_movie_tvshow_properties(id,type,movie_tvshow_details)
            print(f"Completed Updating properties for {title}")


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
    notion_url = os.environ.get('NOTION_URL')
    notion_page_url = os.path.join(notion_url,'pages',id)
    token = os.environ.get('NOTION_TOKEN')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    properties = {}
    if type == 'Film':
        dateType = 'release_date'
    else:
        dateType = 'first_air_date'
    properties['overview'] = {"rich_text":[{"text":{"content":movie_tvshow_details.get('overview','')}}]}
    properties['release_date'] = {"date":{"start":movie_tvshow_details.get(dateType,'')}}
    properties['rating_average'] = {"number":movie_tvshow_details.get('vote_average','')}
    if movie_tvshow_details['poster_path']:
        properties['poster'] = {"files":[{"name":"poster","external":{"url":tmdb_image_url+movie_tvshow_details.get('poster_path')}}]}
    if 'genres' in movie_tvshow_details:
        properties['Genre'] = {}
        properties['Genre']['multi_select'] = []
        for genre in movie_tvshow_details['genres']:
            properties['Genre']['multi_select'].append({'name':genre['name']})
    body = json.dumps({'properties':properties})
    response = requests.request('PATCH',notion_page_url,headers=headers,data=body)
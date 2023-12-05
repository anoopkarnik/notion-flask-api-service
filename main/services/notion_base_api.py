import os
import json
import datetime
import pytz
import requests
import time
import logging

logger = logging.getLogger(__name__)

def query_database(database_id,filters):
    token = os.environ.get('NOTION_TOKEN')
    notion_url = os.environ.get('NOTION_URL')
    notion_database_url = os.path.join(notion_url,'databases')
    notion_database_id_url = os.path.join(notion_database_url,database_id,'query')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }
    has_more = True
    cursor = None
    results = []
    while has_more:
        body = construct_filter_body(filters,cursor)
        logger.info(body)
        response = requests.post(notion_database_id_url,headers=headers,data=body).json()
        # logger.info(response)
        if len(response['results'])>0:
            has_more = response['has_more']
            cursor = response['next_cursor']
            for result in response['results']:
                results.append(modify_result(result))
            return {'results':results}
        else:
            return {'results':[]}


def modify_page(page_id,properties):
    token = os.environ.get('NOTION_TOKEN')
    notion_url = os.environ.get('NOTION_URL')
    notion_page_id_url = os.path.join(notion_url,'pages',page_id)
    token = os.environ.get('NOTION_TOKEN')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    body = construct_update_body(properties)
    logger.info(body)
    response = requests.request('PATCH',notion_page_id_url,headers=headers,data=body).json()
    logger.info(response)
    result = modify_result(response)
    return result

def create_page(database_id,properties):
    token = os.environ.get('NOTION_TOKEN')
    notion_url = os.environ.get('NOTION_URL')
    notion_page_url = os.path.join(notion_url,'pages')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    body = construct_create_body(database_id,properties)
    logger.info(body)
    response = requests.post(notion_page_url,headers = headers, data= body).json()
    logger.info(response)
    result = modify_result(response)
    return result

def add_children_to_page(page_id,children):
    token = os.environ.get('NOTION_TOKEN')
    notion_url = os.environ.get('NOTION_URL')
    notion_page_url = os.path.join(notion_url,'blocks',str(page_id),'children')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    body = construct_children_body(children)
    print(notion_page_url)
    response = requests.patch(notion_page_url,headers = headers, data= body).json()
    logger.info(response)
    return {'message': "Added the children"}

def construct_create_body(database_id,properties):
    body = {}
    body['parent'] = {}
    body['parent']['type'] = 'database_id'
    body['parent']['database_id'] = database_id
    properties_body = {}
    
    # logger.info("Creating body")
    # logger.info(properties)
    for property in properties:
        properties_body[property['name']] = modify_property(property)
    body['properties'] = properties_body
    # logger.info(body)
    return json.dumps(body)

def construct_children_body(children):
    body = {}
    children_body = []
    for child in children:
        children_body.append({child['type']:child['value']})
    logger.info(children_body)
    body['children'] = children_body
    return json.dumps(body)

def construct_filter_body(filters,cursor):
    filters_body = {'filter':{'and':[]}}
    if cursor!=None:
        filters_body['start_cursor'] = cursor
    for filter in filters:
        filters_body['filter']['and'].append(modify_filter(filter))
    return json.dumps(filters_body)
    
def construct_update_body(properties):
    properties_body = {}
    for property in properties:
        properties_body[property['name']] = modify_property(property)
    body = json.dumps({'properties':properties_body})
    return body 

def modify_filter(filter):
    if filter['type'] == 'last_edited_time':
        return {'timestamp':'last_edited_time','last_edited_time':{filter['condition']:filter['value']}}
    elif filter['type'] == 'date':
        return {'property':filter['name'],'date':{filter['condition']:filter['value']}}
    elif filter['type'] == 'checkbox':
        return {'property':filter['name'],'checkbox':{filter['condition']:filter['value']}}
    elif filter['type'] == 'multi_select':
        return {'property':filter['name'],'multi_select':{filter['condition']:filter['value']}}
    elif filter['type'] == 'select':
        return {'property':filter['name'],'select':{filter['condition']:filter['value']}}
    elif filter['type'] == 'created_time':
        return {'timestamp':'created_time','created_time':{filter['condition']:filter['value']}}
    elif filter['type'] == 'relation':
        return {'property':filter['name'],'relation':{filter['condition']:filter['value']}}

def modify_result(result):
    result_body = {}
    result_body['id'] = result['id']
    properties = result['properties']
    # logger.info(properties)
    for prop in properties.keys():
        result_body[prop] = unmodify_property(properties[prop])
    return result_body

def unmodify_property(prop):
    if prop['type'] == 'unique_id':
        return str(prop['unique_id']['prefix']) + '-' + str(prop['unique_id']['number'])
    elif prop['type'] == 'relation':
        return [x['id'] for x in prop['relation']]
    elif prop['type'] == 'number':
        return prop['number']
    elif prop['type'] == 'select':
        return prop['select']['name'] if prop['select'] else None
    elif prop['type'] == 'title':
        return prop['title'][0]['text']['content']
    elif prop['type'] == 'rich_text':
        return prop['rich_text'][0]['text']['content'] if len(prop['rich_text']) > 0 else ''
    elif prop['type'] == 'rollup':
        return unmodify_property(prop['rollup'])
    elif prop['type'] == 'people':
        return [x['name'] for x in prop['people']]
    elif prop['type'] == 'status':
        return prop['status']['name'] if prop['status'] else None
    elif prop['type'] == 'date': 
        return prop['date']['start'] if prop['date'] else None
    elif prop['type'] == 'last_edited_time':
        return prop['last_edited_time']
    elif prop['type'] == 'created_time':
        return prop['created_time']
    elif prop['type'] == 'multi_select':
        return [x['name'] for x in prop['multi_select']]
    elif prop['type'] == 'array':
        return unmodify_property(prop['array'][0]) if len(prop['array']) > 0 else ''

def modify_property(property):
    if property['type'] == 'text':
        return {'rich_text':[{'text':{'content':property['value']}}]}
    elif property['type'] == 'title':
        return {'title':[{'text':{'content':property['value']}}]}
    elif property['type'] == 'date':
        return {'date':{'start':property['value'] if property['value'] else '1900-01-01'}}
    elif property['type'] == 'number':
        return {'number':property['value']}
    elif property['type'] == 'file_url':
        return {'files':[{'type':'external','name':'Cover','external':{'url':property['value']}}]}
    elif property['type'] =='url':
        return {'url':property['value']}
    elif property['type'] == 'select':
        return {'select':{'name':property['value']}}
    elif property['type'] == 'multi_select':
        result = {'multi_select':[]}
        for value in property['value']:
            result['multi_select'].append({'name':value})
        return result
    elif property['type'] == 'relation':
        result = {'relation':[]}
        for value in property['value']:
            result['relation'].append({'id':value})
        return result
import os
import json
import datetime
import pytz
import requests
import time
import logging
from ..clients.notion_client import query_database,create_page,modify_page,create_database,get_page,get_block_children,delete_block,append_block_children

logger = logging.getLogger(__name__)

def query_notion_database(database_id,filters):
    has_more = True
    cursor = None
    results = []
    while has_more:
        body = construct_filter_body(filters,cursor)
        #logger.info(f'constructed filter body - {body}')
        response = query_database(database_id,body)
        #logger.info(response)
        if len(response['results'])>0:
            has_more = response['has_more']
            cursor = response['next_cursor']
            for result in response['results']:
                results.append(modify_result(result))
        else:
            has_more = False
    return {'results':results}


def construct_filter_body(filters,cursor):
    filters_body = {'filter':{'and':[]}}
    if cursor!=None:
        filters_body['start_cursor'] = cursor
    for filter in filters:
        filters_body['filter']['and'].append(modify_filter(filter))
    return filters_body

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
    # #logger.info(properties)
    for prop in properties.keys():
        result_body[prop] = unmodify_property(properties[prop])
    return result_body

def query_page_blocks(page_id,type):
    response = get_block_children(page_id)
    logger.info(response)
    if len(response['results'])>0:
        if type == 'parent':
            results = {}
            for result in response['results']:
                try:
                    parent_result = modify_block(result)
                    parent_result_id = parent_result['id']
                    parent_result_name = parent_result['name']
                    child_results = query_page_blocks(parent_result_id,'child')
                    results[parent_result_name] ={}
                    results[parent_result_name]['id'] = parent_result_id
                    results[parent_result_name]['children'] = child_results
                except:
                    logger.info(f"Error in {result}")
            return results
        elif type == 'child':
            results = []
            for result in response['results']:
                child_result = modify_block(result)
                child_result_name = child_result['name']
                if '\n' in child_result_name:
                    results.extend(child_result_name.split('\n'))
                else:
                    results.append(child_result_name)
            return results
    #logger.info(results)
    return []


def modify_block(block):
    block_result = {}
    if 'heading_3' in block:
        block_result['name'] = block['heading_3']['rich_text'][0]['text']['content']
        if block['has_children']:
            block_result['id'] = block['id']
    elif 'numbered_list_item' in block:
        block_result['name'] = block['numbered_list_item']['rich_text'][0]['text']['content']
        if block['has_children']:
            block_result['id'] = block['id']
    elif 'code' in block:
        block_result['name'] = block['code']['rich_text'][0]['text']['content']
        if block['has_children']:
            block_result['id'] = block['id']
    return block_result

def modify_notion_page(page_id,properties):
    body = construct_update_body(properties)
    logger.info(body)
    response = modify_page(page_id,body)
    logger.info(response)
    result = modify_result(response)
    return result

def construct_update_body(properties):
    #logger.info(properties)
    properties_body = {}
    for property in properties:
        properties_body[property['name']] = modify_property(property)
    body = {'properties':properties_body}
    return body 

def create_notion_page(database_id,properties):
    body = construct_create_body(database_id,properties)
    #logger.info(body)
    response = create_page(body)
    #logger.info(response)
    result = modify_result(response)
    return result

def construct_create_body(database_id,properties):
    body = {}
    body['parent'] = {}
    body['parent']['type'] = 'database_id'
    body['parent']['database_id'] = database_id
    properties_body = {}
    
    # #logger.info("Creating body")
    # #logger.info(properties)
    for property in properties:
        properties_body[property['name']] = modify_property(property)
    body['properties'] = properties_body
    # #logger.info(body)
    return body

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
    elif property['type'] == 'checkbox':
        return {'checkbox':property['value']}
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

def add_children_to_page(page_id,children):
    body = construct_children_body(children)
    response = append_block_children(page_id,body)
    #logger.info(response)
    return {'message': "Added the children"}

def construct_children_body(children):
    body = {}
    children_body_list = []
    for child in children:
        children_body = {}
        children_body[child['type']] = modify_children_property(child)
        children_body_list.append(children_body)
    body['children'] = children_body_list
    #logger.info(body)
    return body

def modify_children_property(prop):
    if prop['type'] == 'table_of_contents':
        return {'color':'default'}
    elif prop['type'] == 'callout':
        return prop['value']
    elif prop['type'] == 'embed':
        return {'url':prop['value']}
    else:
        return {'rich_text':[{'text':{'content':prop['value']}}]}
    
def delete_page_blocks(page_id):
    response = get_block_children(page_id)
    #logger.info(response)
    if len(response['results'])>0:
        for result in response['results']:
            delete_block(result['id'])
    return {'message': "Deleted the children"}

def get_notion_page(page_id):
    response = get_page(page_id)
    #logger.info(response)
    result = modify_result(response)
    return result

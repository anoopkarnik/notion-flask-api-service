import os
import json
import datetime
import pytz
import requests
import time
import logging

logger = logging.getLogger(__name__)
token = os.environ.get('NOTION_TOKEN')
notion_url = os.environ.get('NOTION_URL')

def create_database(parent,title,properties):
    url = f"{notion_url}/databases"
    payload = {
        "parent": { "type": "page_id", "page_id": parent },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": title
                }
            }
        ],
        "properties": properties
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }
    response = requests.post(url,headers=headers,json=payload).json()
    return response

def query_database(database_id,filters_body):
    url = f"{notion_url}/databases/{database_id}/query"
    logger.info(url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }
    response = requests.post(url,headers=headers,json=filters_body).json()
    logger.info(response)
    return response
    
def create_page(body):
    url = f"{notion_url}/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }
    response = requests.post(url,headers=headers,json=body).json()
    return response

def modify_page(page_id,body):
    url = f"{notion_url}/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }
    response = requests.patch(url,headers=headers,json=body).json()
    return response

def get_page(page_id):
    url = f"{notion_url}/pages/{page_id}"
    # logger.info(url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22"
    }
    response = requests.get(url,headers=headers).json()
    return response

def get_block_children(id):
    url = f"{notion_url}/blocks/{id}/children?page_size=100"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22"
    }
    response = requests.get(url,headers=headers).json()
    return response

def delete_block(id):
    url = f"{notion_url}/blocks/{id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22"
    }
    response = requests.delete(url,headers=headers).json()
    return response

def append_block_children(id,children):
    url = f"{notion_url}/blocks/{id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }
    response = requests.patch(url,headers=headers,json=children).json()
    return response

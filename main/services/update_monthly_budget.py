import os
import json
import datetime
import pytz
import requests

def get_financial_transaction_details():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    local_time = datetime.datetime.now()
    filter = {"and":[]}
    filter['and'].append({"property":"Monthly Budget","relation":{"is_not_empty":True}})
    filter['and'].append({"timestamp":"created_time","created_time":{"before":f"{local_time.year}-{local_time.month}-01"}})
    notion_financial_url = os.path.join(notion_url,'databases',os.environ.get('FINANCIAL_TRANSACTION_DB_ID'),"query")
    results = requests.post(notion_financial_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[])
    for result in results:
        update_transaction_details(result)


def update_transaction_details(result):
    notion_url = os.environ.get('NOTION_URL')
    notion_page_id_url = os.path.join(notion_page_url,'pages',id)
    token = os.environ.get('NOTION_TOKEN')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    properties = {}
    relation_ids = [relation['id'] for relation in result['properties']['Monthly Budget']['relation']]
    properties['Old Monthly Budget'] = {}
    properties['Old Monthly Budget']['relation'] =[]
    for relation_id in relation_ids:
        properties['Old Monthly Budget']['relation'].append({'id':relation_id})
    properties['Monthly Budget'] ={}
    properties['Monthly Budget']['relation'] = []
    body = json.dumps({'properties':properties})
    response = requests.request('PATCH',notion_page_id_url,headers=headers,data=body)
    return result

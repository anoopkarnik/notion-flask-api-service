import os
import json
import datetime
import pytz
import requests
from ..services.notion_base_api import query_database,create_page,modify_page
import logging

logger = logging.getLogger(__name__)

def get_financial_transaction_details():
    local_time = datetime.datetime.now()
    filters = []
    filters.append({'name':'Monthly Budget','type':'relation','condition':'is_not_empty','value':True})
    filters.append({'type':'created_time','condition':'before','value':f"{local_time.year}-{local_time.month}-01"})
    results = query_database(os.environ.get('FINANCIAL_TRANSACTION_DB_ID'),filters).get('results',[])
    for result in results:
        update_transaction_details(result)


def update_transaction_details(result):
    properties = []
    properties.append({'name':'Old Monthly Budget','type':'relation','value':[x['id'] for x in result['Monthly Budget']]})
    properties.append({'name':'Monthly Budget','type':'relation','value':[]})
    response = modify_page(result['id'],properties)
    return response

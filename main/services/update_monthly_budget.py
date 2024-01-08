import os
import json
import datetime
import pytz
import requests
from ..services.notion_base_api import query_notion_database,create_notion_page,modify_notion_page
import logging

logger = logging.getLogger(__name__)

def get_financial_transaction_details():
    local_time = datetime.datetime.now()
    filters = []
    filters.append({'name':'Monthly Budget','type':'relation','condition':'is_not_empty','value':True})
    month = local_time.month if local_time.month > 9 else f"0{local_time.month}"
    filters.append({'type':'created_time','condition':'before','value':f"{local_time.year}-{month}-01"})
    results = query_notion_database(os.environ.get('FINANCIAL_TRANSACTION_DB_ID'),filters).get('results',[])
    for result in results:
        update_transaction_details(result)


def update_transaction_details(result):
    # logger.info(f"Updating transaction details for {result}")
    properties = []
    properties.append({'name':'Old Monthly Budget','type':'relation','value':[x for x in result['Monthly Budget']]})
    properties.append({'name':'Monthly Budget','type':'relation','value':[]})
    response = modify_notion_page(result['id'],properties)
    return response

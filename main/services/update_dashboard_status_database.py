import os
import json
import datetime
import pytz
import requests
from ..services.notion_base_api import query_notion_database,create_notion_page,modify_notion_page
import logging

logger = logging.getLogger(__name__)

def create_dashboard_status_updates_page():
    task_details = get_task_details()
    scheduled_planner_details = get_scheduled_planner_details()
    interesting_details = get_interesting_details()
    quick_capture_details = get_quick_capture_details()
    journal_details = get_journal_details()
    database_id = os.environ.get('DASHBOARD_STATUS_UPDATES_DB_ID')
    properties = []
    properties.append({'name':'Name','type':'title','value':'Dashboard Update'})
    properties.append({'name':'Urgent Important Tasks','type': 'number','value':task_details['imp_urg_no']})
    properties.append({'name':'Important Not Urgent Tasks','type': 'number','value':task_details['imp_not_urg_no']})
    properties.append({'name':'Not Important Urgent Tasks','type':'number','value':task_details['not_imp_urg_no']})
    properties.append({'name':'Not Important Not Urgent Tasks','type': 'number','value':task_details['not_imp_not_urg_no']})
    properties.append({'name':'Schedule Tasks','type': 'number','value':scheduled_planner_details['task_no']})
    properties.append({'name':'Schedule Habits','type': 'number','value':scheduled_planner_details['habit_no']})
    properties.append({'name':'Schedule Financial Tasks','type': 'number','value':scheduled_planner_details['financial_task_no']})
    properties.append({'name':'Total Interesting Things','type': 'number','value':interesting_details['total_no']})
    properties.append({'name':'Weekly Interesting Things','type': 'number','value':interesting_details['week_back_no']})
    properties.append({'name':'Monthly Interesting Things','type': 'number','value':interesting_details['month_back_no']})
    properties.append({'name':'Unmoved Quick Captures','type': 'number','value':quick_capture_details['total_no']})
    properties.append({'name':'Uncategorized Journals','type': 'number','value':journal_details['total_no']})
    response = create_notion_page(database_id,properties)

def get_task_details():
    result = {}
    filters = []
    filters.append({'name':'Done','type':'checkbox','condition':'equals','value':False})
    filters.append({'name':'Urgent','type':'checkbox','condition':'equals','value':True})
    filters.append({'name':'Important','type':'checkbox','condition':'equals','value':True})
    result['imp_urg_no'] = len(query_notion_database(os.environ.get('TASKS_DB_ID'),filters).get('results',[]))
    filters[1]['value'] = False
    result['imp_not_urg_no'] = len(query_notion_database(os.environ.get('TASKS_DB_ID'),filters).get('results',[]))
    filters[2]['value'] = False
    result['not_imp_not_urg_no'] = len(query_notion_database(os.environ.get('TASKS_DB_ID'),filters).get('results',[]))
    filters[1]['value'] = True
    result['not_imp_urg_no'] = len(query_notion_database(os.environ.get('TASKS_DB_ID'),filters).get('results',[]))
    return result

def get_scheduled_planner_details():
    result = {}
    filters = []
    filters.append({'name':'Tags','type':'multi_select','condition':'contains','value':'Task'})
    filters.append({'name':'Completed','type':'checkbox','condition':'equals','value':False})
    filters.append({'name':'Not Completed','type':'checkbox','condition':'equals','value':False})
    result['task_no'] = len(query_notion_database(os.environ.get('CALENDAR_DB_ID'),filters).get('results',[]))
    filters[0]['value']= "Habit"
    result['habit_no'] = len(query_notion_database(os.environ.get('CALENDAR_DB_ID'),filters).get('results',[]))
    filters[0]['value'] = "Financial"
    result['financial_task_no'] = len(query_notion_database(os.environ.get('CALENDAR_DB_ID'),filters).get('results',[]))
    return result

def get_interesting_details():
    result = {}
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    filters = []
    filters.append({'name':'Checkbox','type':'checkbox','condition':'equals','value':False})
    result['total_no'] = len(query_notion_database(os.environ.get('INTERESTING_DB_ID'),filters).get('results',[]))
    filters.append({'type':'created_time','condition':'on_or_after','value':one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    result['week_back_no'] = len(query_notion_database(os.environ.get('INTERESTING_DB_ID'),filters).get('results',[]))
    filters[1]['value'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(query_notion_database(os.environ.get('INTERESTING_DB_ID'),filters).get('results',[]))
    return result

def get_quick_capture_details():
    result = {}
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    filters = []
    result['total_no'] = len(query_notion_database(os.environ.get('QUICK_CAPTURE_DB_ID'),filters).get('results',[]))
    filters.append({'type':'created_time','condition':'on_or_after','value':one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    result['week_back_no'] = len(query_notion_database(os.environ.get('QUICK_CAPTURE_DB_ID'),filters).get('results',[]))
    filters[0]['value'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(query_notion_database(os.environ.get('QUICK_CAPTURE_DB_ID'),filters).get('results',[]))
    return result
    
def get_areas_details():
    result = {}
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    filters = []
    filters.append({'type':'created_time','condition':'on_or_after','value':one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    result['week_back_no'] = len(query_notion_database(os.environ.get('AREAS_DB_ID'),filters).get('results',[]))
    filters[0]['value'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(query_notion_database(os.environ.get('AREAS_DB_ID'),filters).get('results',[]))
    return result

def get_journal_details():
    result = {}
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    filters = []
    filters.append({'name':'Type','type':'multi_select','condition':'is_empty','value':True})
    result['total_no'] = len(query_notion_database(os.environ.get('JOURNAL_DB_ID'),filters).get('results',[]))
    filters.append({'type':'created_time','condition':'on_or_after','value':one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")})
    result['week_back_no'] = len(query_notion_database(os.environ.get('JOURNAL_DB_ID'),filters).get('results',[]))
    filters[1]['value'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(query_notion_database(os.environ.get('JOURNAL_DB_ID'),filters).get('results',[]))
    return result
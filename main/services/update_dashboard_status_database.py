import os
import json
import datetime
import pytz
import requests



def create_dashboard_status_updates_page():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    task_details = get_task_details()
    scheduled_planner_details = get_scheduled_planner_details()
    interesting_details = get_interesting_details()
    quick_capture_details = get_quick_capture_details()
    journal_details = get_journal_details()
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    notion_page_url = os.path.join(notion_url,'pages')
    body = {}
    body['parent'] = {}
    body['parent']['type'] = 'database_id'
    body['parent']['database_id'] = os.environ.get('DASHBOARD_STATUS_UPDATES_DB_ID')
    properties = {}
    properties['Name'] = {'title':[{'text':{'content':'Dashboard Update'}}]}
    properties['Urgent Important Tasks'] = {'number':task_details['imp_urg_no']}
    properties['Important Not Urgent Tasks'] = {'number':task_details['imp_not_urg_no']}
    properties['Not Important Urgent Tasks'] = {'number':task_details['not_imp_urg_no']}
    properties['Not Important Not Urgent Tasks'] = {'number':task_details['not_imp_not_urg_no']}
    properties['Schedule Tasks'] = {'number':scheduled_planner_details['task_no']}
    properties['Schedule Habits'] = {'number':scheduled_planner_details['habit_no']}
    properties['Schedule Financial Tasks'] = {'number':scheduled_planner_details['financial_task_no']}
    properties['Total Interesting Things'] = {'number':interesting_details['total_no']}
    properties['Weekly Interesting Things'] = {'number':interesting_details['week_back_no']}
    properties['Monthly Interesting Things'] = {'number':interesting_details['month_back_no']}
    properties['Unmoved Quick Captures'] = {'number':quick_capture_details['total_no']}
    properties['Uncategorized Journals'] = {'number':journal_details['total_no']}
    body['properties'] = properties
    response = requests.post(notion_page_url,headers=headers,data=json.dumps(body))

def get_task_details():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    result = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    filter = {"and":[]}
    filter['and'].append({"property":"Done","checkbox":{"equals":False}})
    filter['and'].append({"property":"Urgent","checkbox":{"equals":True}})
    filter['and'].append({"property":"Important","checkbox":{"equals":True}})
    notion_task_url = os.path.join(notion_url,'databases',os.environ.get('TASKS_DB_ID'),"query")
    result['imp_urg_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][1]['checkbox']['equals'] = False
    result['imp_not_urg_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][2]['checkbox']['equals'] = False
    result['not_imp_not_urg_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][1]['checkbox']['equals'] = True
    result['not_imp_urg_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    return result

def get_scheduled_planner_details():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    result = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    filter = {"and":[]}
    filter['and'].append({"property":"Tags","multi_select":{"contains":"Task"}})
    filter['and'].append({"property":"Completed","checkbox":{"equals":False}})
    filter['and'].append({"property":"Not Completed","checkbox":{"equals":False}})
    notion_task_url = os.path.join(notion_url,'databases',os.environ.get('SCHEDULED_PLANNER_DB_ID'),"query")
    result['task_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][0]['multi_select']['contains'] = "Habit"
    result['habit_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][0]['multi_select']['contains'] = "Financial"
    result['financial_task_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    return result

def get_interesting_details():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    notion_task_url = os.path.join(notion_url,'databases',os.environ.get('INTERESTING_DB_ID'),"query")
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    result = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    filter = {"property":"Checkbox","checkbox":{"equals":False}}
    result['total_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter = {"and":[]}
    filter['and'].append({"property":"Checkbox","checkbox":{"equals":False}})
    filter['and'].append({"property":"created_time","created_time":{"on_or_after":one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")}})
    result['week_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][1]['created_time']['on_or_after'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    return result

def get_quick_capture_details():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    notion_task_url = os.path.join(notion_url,'databases',os.environ.get('QUICK_CAPTURE_DB_ID'),"query")
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    result = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    result['total_no'] = len(requests.post(notion_task_url,headers=headers).json().get('results',[]))
    filter = {"property":"created_time","created_time":{"on_or_after":one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")}}
    result['week_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['created_time']['on_or_after'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    return result
    
def get_areas_details():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    result = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    filter = {"property":"created_time","created_time":{"on_or_after":one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")}}
    notion_task_url = os.path.join(notion_url,'databases',os.environ.get('AREAS_DB_ID'),"query")
    result['week_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][0]['created_time']['on_or_after'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    return result

def get_journal_details():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    notion_task_url = os.path.join(notion_url,'databases',os.environ.get('JOURNAL_DB_ID'),"query")
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    one_week_back_gmt = current_time_gmt - datetime.timedelta(days=7)
    one_month_back_gmt = current_time_gmt - datetime.timedelta(days=30)
    result = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    result['total_no'] = len(requests.post(notion_task_url,headers=headers).json().get('results',[]))
    filter = {"and":[]}
    filter['and'].append({"property":"Type","multi_select":{"is_empty":True}})
    filter['and'].append({"property":"created_time","created_time":{"on_or_after":one_week_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")}})
    result['week_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    filter['and'][1]['created_time']['on_or_after'] = one_month_back_gmt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['month_back_no'] = len(requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json().get('results',[]))
    return result
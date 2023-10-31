import os
import json
import datetime
import pytz
import requests
import schedule
import time



def create_calender_page():
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    notion_page_url = os.path.join(notion_url,'pages')
    body = {}
    body['parent'] = {}
    body['parent']['type'] = 'database_id'
    body['parent']['database_id'] = os.environ.get('CALENDAR_DB_ID')
    scheduler_details = get_scheduler_details()
    for scheduler_detail in scheduler_details.get('results'):
        page_id = scheduler_detail['id']
        notion_page_id_url =  os.path.join(notion_page_url,page_id)
        data = scheduler_detail['properties']
        properties = {}
        properties['Name'] = {'title':[{'text':{'content':data['Name']['title'][0]['text']['content']}}]}
        properties['Tags'] = {'multi_select':[{'name':data['Type']['select']['name']}]}
        body['properties'] = properties
        repeat_type = data['Repeat Type']['select']['name']
        time = data['Time']['rich_text'][0]['text']['content']
        time_zone = data['Time Zone']['select']['name']
        repeat_number = data['Repeat Number']['number']
        local_tz = pytz.timezone(time_zone)
        local_time = datetime.datetime.now(local_tz)
        start_date = datetime.datetime.strptime(data['Start Date']['date']['start'])
        scheduled_time = local_tz.localize(datetime.datetime.strptime(time, '%H%M').replace(year=start_date.year, month=start_date.month, day=start_date.day))
        time_since_last_trigger = None
        triggered = False
        if data['Last Triggered Date']['date']:
            last_triggered_time = data['Last Triggered Date']['date']['start']
            local_last_triggered_time = local_tz.localize(datetime.datetime.strptime(last_triggered_time,'%Y-%m-%d'))
            time_since_last_trigger = local_time - local_last_triggered_time
        # print(f"{local_time}")
        # print(f"Triggered {data['Name']['title'][0]['text']['content']} - {scheduled_time} - {local_last_triggered_time}")
        if repeat_type == 'off':
            continue
        elif repeat_type == 'daily':
            if time_since_last_trigger and time_since_last_trigger.days < repeat_number:
                continue
            if 0 < ((local_time - scheduled_time).total_seconds())/60 < 30:
                local_last_triggered_time = local_time
                triggered = True
                # print(f"Triggered {data['Name']['title'][0]['text']['content']} - {scheduled_time}")
        elif repeat_type == 'weekly':
            days_of_week = [x['name'] for x in data['Days Of Week']['multi_select']]
            if time_since_last_trigger and time_since_last_trigger.days < 7 * repeat_number:
                continue
            if local_time.strftime("%A") in days_of_week and 0 < ((local_time - scheduled_time).total_seconds())/60 <30:
                local_last_triggered_time = local_time
                triggered = True
                # print(f"Triggered {data['Name']['title'][0]['text']['content']} - {scheduled_time}")
        elif repeat_type == 'monthly':
            if time_since_last_trigger and time_since_last_trigger.days < 30 * repeat_number:
                continue
            if local_time.day == scheduled_time.day and 0 < ((local_time - scheduled_time).total_seconds())/60 <30:
                local_last_triggered_time = local_time
                triggered = True
                # print(f"Triggered {data['Name']['title'][0]['text']['content']} - {scheduled_time}")
        elif repeat_type == 'yearly':
            if time_since_last_trigger and time_since_last_trigger.days < 365 * repeat_number:
                continue
            if local_time.day == scheduled_time.day and local_time.month == scheduled_time.month and 0 < ((local_time - scheduled_time).total_seconds())/60 <30:
                local_last_triggered_time = local_time
                triggered = True
                # print(f"Triggered {data['Name']['title'][0]['text']['content']} - {scheduled_time}"
        if triggered:
            response = requests.post(notion_page_url,headers=headers,data=json.dumps(body))
            if response.status_code!=200:
                print(response.json())
            page_properties = {}
            page_properties['Last Triggered Date'] = {"date":{"start":local_last_triggered_time.strftime("%Y-%m-%d")}}
            page_body = json.dumps({'properties':page_properties})
            response = requests.request('PATCH',notion_page_id_url,headers=headers,data=page_body)
            if response.status_code!=200:
                print(response.json())


def get_scheduler_details():
    gmt_timezone = pytz.timezone('GMT')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    notion_url = os.environ.get('NOTION_URL')
    token = os.environ.get('NOTION_TOKEN')
    result = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version":"2022-02-22",
        "Content-Type":"application/json"
    }
    filter = {"property":"Start Date","date":{"on_or_after":current_time_gmt.strftime("%Y-%m-%d")}}
    notion_task_url = os.path.join(notion_url,'databases',os.environ.get('SCHEDULER_DB_ID'),"query")
    result = requests.post(notion_task_url,headers=headers,data=json.dumps({'filter':filter})).json()
    return result
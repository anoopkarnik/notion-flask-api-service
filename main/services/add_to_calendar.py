import os
import json
import datetime
import pytz
import requests
import time
from ..services.notion_base_api import query_database,create_page,modify_page
import logging

logger = logging.getLogger(__name__)


def create_calendar_page():
    database_id = os.environ.get('CALENDAR_DB_ID')
    location = get_current_location()
    print(f"My current location is {location}")
    scheduler_details = get_scheduler_details(location)
    for row in scheduler_details:
        page_id = row['id']
        properties = []
        properties.append({'name':'Name','type':'title','value':row.get('Name')})
        properties.append({'name':'Tags','type':'multi_select','value':[row.get('Type')]})
        repeat_type = row['Repeat Type']
        time = row['Time']
        time_zone = row['Time Zone']
        repeat_number = row['Repeat Number']
        local_tz = pytz.timezone(time_zone)
        local_time = datetime.datetime.now(local_tz)
        start_date = local_tz.localize(datetime.datetime.strptime(row['Start Date'],'%Y-%m-%d'))
        if start_date < local_time and (repeat_type == 'daily' or repeat_type == 'weekly') :
            start_date = local_time
        scheduled_time = local_tz.localize(datetime.datetime.strptime(time, '%H%M').replace(year=start_date.year, month=start_date.month, day=start_date.day))
        time_since_last_trigger = None
        triggered = False
        if row['Last Triggered Date']:
            last_triggered_time = row['Last Triggered Date']
            local_last_triggered_time = local_tz.localize(datetime.datetime.strptime(last_triggered_time,'%Y-%m-%d'))
            time_since_last_trigger = local_time - local_last_triggered_time
        # logger.info(f"{local_time}")
        # logger.info(f"Triggered {data['Name']['title'][0]['text']['content']} - {scheduled_time} - {local_last_triggered_time}")
        if repeat_type == 'off':
            continue
        elif repeat_type == 'daily':
            if time_since_last_trigger and time_since_last_trigger.days < repeat_number:
                continue
            if 0 < ((local_time - scheduled_time).total_seconds())/60 < 35:
                local_last_triggered_time = local_time
                triggered = True
                logger.info(f"Triggered {row['Name']} - {scheduled_time}")
        elif repeat_type == 'weekly':
            days_of_week = row['Days Of Week']
            if time_since_last_trigger and time_since_last_trigger.days < 7 * repeat_number:
                continue
            if local_time.strftime("%A") in days_of_week and 0 < ((local_time - scheduled_time).total_seconds())/60 <35:
                local_last_triggered_time = local_time
                triggered = True
                logger.info(f"Triggered {row['Name']} - {scheduled_time}")
        elif repeat_type == 'monthly':
            if time_since_last_trigger and time_since_last_trigger.days < 30 * repeat_number:
                continue
            if local_time.day == scheduled_time.day and 0 < ((local_time - scheduled_time).total_seconds())/60 <35:
                local_last_triggered_time = local_time
                triggered = True
                logger.info(f"Triggered {row['Name']} - {scheduled_time}")
        elif repeat_type == 'yearly':
            if time_since_last_trigger and time_since_last_trigger.days < 365 * repeat_number:
                continue
            if local_time.day == scheduled_time.day and local_time.month == scheduled_time.month and 0 < ((local_time - scheduled_time).total_seconds())/60 <35:
                local_last_triggered_time = local_time
                triggered = True
                logger.info(f"Triggered {row['Name']} - {scheduled_time}")
        if triggered:
            logger.info("Started Creating Page")
            response = create_page(database_id,properties)
            logger.info("Created Page")
            logger.info(response)
            page_properties = []
            page_properties.append({'name':'Last Triggered Date','type':'date','value':local_last_triggered_time.strftime("%Y-%m-%d")})
            logger.info("Started Modifying Page")
            response = modify_page(page_id,page_properties)
            logger.info("Modified Page")
            logger.info(response)


def get_scheduler_details(location):
    gmt_timezone = pytz.timezone('Asia/Kolkata')
    current_time_gmt = datetime.datetime.now(gmt_timezone)
    filters = []
    filters.append({"name":"Start Date",'type':"date",'condition':"on_or_before",'value':current_time_gmt.strftime("%Y-%m-%d")})
    filters.append({'name':'Location','type':'multi_select','condition':'contains','value':location})
    logger.info("Querying Database")
    results = query_database(os.environ.get('SCHEDULER_DB_ID'),filters).get('results',[])
    logger.info("Queried Database")
    return results

def get_current_location():
    filters = []
    filters.append({"name":"End Time",'type':'date','condition':'is_empty','value':True})
    logger.info("Querying Database")
    results = query_database(os.environ.get('TIMEBOX_DB_ID'),filters).get('results',[])
    logger.info("Queried Database")
    if len(results) == 0:
        return 'Home'
    else:
        for row in results:
            if row['Action Name'] == 'Parents':
                return row['Action Name']
            elif row['Action Name'] == 'Short Vacation':
                return row['Action Name']
            elif row['Action Name'] == 'Long Vacation':
                return row['Action Name']
    return 'Home'
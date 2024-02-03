import requests
import os
import json
import datetime
import pytz  # This library helps with time zone handling
from ..services.notion_base_api import query_notion_database,get_notion_page
import logging

logger = logging.getLogger(__name__)


def get_project_details():
    projects_db_id = os.environ.get('PROJECTS_DB_ID')
    filters,sorts = [],[]
    filters.append({'name':'Status','type':'status','condition':'does_not_equal','value': 'Not Started'})
    filters.append({'name':'Status','type':'status','condition':'does_not_equal','value': 'Cancelled'})
    filters.append({'name':'Parent project', 'type':'relation', 'condition':'is_empty', 'value':True})
    projects = query_notion_database(projects_db_id,filters,sorts).get('results',[])
    for project in projects:
        # project['Frameworks'] = get_relations_details(project['Frameworks'])
        # project['Languages'] = get_relations_details(project['Languages'])
        # project['PlaceOfWork/Education'] = get_relations_details(project['PlaceOfWork/Education'])
        # project['Tools'] = get_relations_details(project['Tools'])
        yield project



def get_complete_portfolio():
    result = {}
    pow_db_id = os.environ.get('POW_DB_ID')
    filters,sorts = [],[]
    filters.append({"name":"Education Type","type":"select","condition":"is_not_empty","value":True})
    sorts.append({"name":"Start Date","type":"date","direction":"descending"})
    education = query_notion_database(pow_db_id,filters,sorts).get('results',[])
    education = add_relation_details_to_results(education,'Projects')
    filters,sorts = [],[]
    filters.append({"name":"Type","type":"multi_select","condition":"contains","value":'Full Time'})
    sorts.append({"name":"Start Date","type":"date","direction":"descending"})
    works = query_notion_database(pow_db_id,filters,sorts).get('results',[])
    works = add_relation_details_to_results(works,'Projects')
    filters,sorts = [],[]
    filters.append({"name":"Type","type":"multi_select","condition":"contains","value":'Internship'})
    sorts.append({"name":"Start Date","type":"date","direction":"descending"})
    internships = query_notion_database(pow_db_id,filters,sorts).get('results',[])
    internships = add_relation_details_to_results(internships,'Projects')
    filters,sorts = [],[]
    filters.append({"name":"Type","type":"multi_select","condition":"contains","value":'Part Time'})
    sorts.append({"name":"Start Date","type":"date","direction":"descending"})
    part = query_notion_database(pow_db_id,filters,sorts).get('results',[])
    part = add_relation_details_to_results(part,'Projects')
    filters,sorts = [],[]
    filters.append({"name":"Type","type":"multi_select","condition":"contains","value":'Self Employed'})
    sorts.append({"name":"Start Date","type":"date","direction":"descending"})
    self_employed = query_notion_database(pow_db_id,filters,sorts).get('results',[])
    self_employed = add_relation_details_to_results(self_employed,'Projects')
    result['education'] = education
    result['works'] = works
    result['internships'] = internships
    result['part_time_work'] = part
    result['self_employed'] = self_employed
    return result

def add_relation_details_to_results(results,relation_name):
    results_new = []
    for result in results:
        result[relation_name] = get_relations_details(result[relation_name])
        results_new.append(result)
    return results_new

def get_relations_details(relation_ids):
    results = []
    for relation_id in relation_ids:
        results.append(get_notion_page(relation_id))
    return results
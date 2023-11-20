from ..services.update_book_database import update_books
from ..services.update_movie_tvshow_database import update_movies_tvshows
from ..services.update_dashboard_status_database import create_dashboard_status_updates_page
from ..services.add_to_calendar import create_calendar_page
from ..services.notion_base_api import query_database,create_page,modify_page
from ..services.update_monthly_budget import get_financial_transaction_details
import logging

# Initialize the scheduler
def schedule_jobs(scheduler):
    logging.info('Scheduling jobs...')
    # Schedule update_dashboard_status() to run daily at a specific time
    job = scheduler.add_job(
        func=create_dashboard_status_updates_page,
        trigger='interval',
        minutes=60,
        id='create new dashboard status',
        name='create new dashboard status',
        replace_existing=True)
    logging.info(f"Scheduled job: {job.name}")

    # Schedule update_movie_tvshow() to run every 30 minutes
    job = scheduler.add_job(
        func=update_movies_tvshows,
        trigger='interval',
        minutes=5,
        id='update_movie_tvshow_job',
        name='Update movie and TV show database every 30 minutes',
        replace_existing=True)
    logging.info(f"Scheduled job: {job.name}")
    
    job = scheduler.add_job(
        func=create_calendar_page,
        trigger='interval',
        minutes=30,
        id='update_movie_tvshow_job',
        name='Update movie and TV show database every 30 minutes',
        replace_existing=True)
    logging.info(f"Scheduled job: {job.name}")

    job = scheduler.add_job(
        func=update_books,
        trigger='interval',
        minutes=1,
        id='update_books_job',
        name='Update books every 30 minutes',
        replace_existing=True)
    logging.info(f"Scheduled job: {job.name}")

    job = scheduler.add_job(
        func=get_financial_transaction_details,
        trigger='interval',
        minutes=30,
        id='update_financial_transaction_details',
        name='Update financial transaction details',
        replace_existing=True)
    logging.info(f"Scheduled job: {job.name}")

    # Start the scheduler
    try:
        scheduler.start()
        logging.info('Scheduler started successfully.')
    except Exception as e:
        logging.error('Failed to start the scheduler', exc_info=True)
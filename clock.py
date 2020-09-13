from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app import update_users

scheduler = BackgroundScheduler()
scheduler.add_job(update_users, CronTrigger.from_crontab('* 11-23 * * *'), timezone=pytz.timezone('US/Pacific'))
# scheduler.add_job(refresh_games_db, 'interval', days=1, start_date='2020-09-10 00:00:00')
scheduler.start()


from pytz import utc

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from app import api_handlers_admin
from app import app
from app import models
from util import tag_manage
from util import db_organize
from util import flatten_history

jobstores = {
	'default': MemoryJobStore()
}
executors = {
	'default': {'type': 'threadpool', 'max_workers': 5},
}
job_defaults = {
	'coalesce': True,
	'max_instances': 3
}
scheduler = BlockingScheduler()

# .. do something else here, maybe add jobs etc.

scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)

def minutes(count):
	return count * 60
def hours(count):
	return count * minutes(60)
def days(count):
	return count * hours(24)


def flatten_series_by_url():
	with app.app_context():
		api_handlers_admin.flatten_series_by_url(None, admin_override=True)
def consolidate_rrl_items():
	with app.app_context():
		api_handlers_admin.consolidate_rrl_items(None, admin_override=True)
def delete_duplicate_releases():
	with app.app_context():
		api_handlers_admin.delete_duplicate_releases(None, admin_override=True)
def fix_escaped_quotes():
	with app.app_context():
		api_handlers_admin.fix_escaped_quotes(None, admin_override=True)
def clean_tags():
	with app.app_context():
		api_handlers_admin.clean_tags(None, admin_override=True)
def delete_bad_tags():
	with app.app_context():
		api_handlers_admin.delete_bad_tags(None, admin_override=True)
def clean_garbage_releases():
	with app.app_context():
		api_handlers_admin.clean_bad_releases(None, admin_override=True)
def trim_spaces():
	with app.app_context():
		api_handlers_admin.clean_spaces(None, admin_override=True)
def update_materialized_view():
	with app.app_context():
		models.refresh_materialized_view()

def update_to_merge_series_list():
	builder = db_organize.MatchLogBuilder()
	db_organize.levenshein_merger_series(interactive=False, builder=builder)
	db_organize.release_merger_series(interactive=False, builder=builder)

def update_to_merge_groups_list():
	builder = db_organize.MatchLogBuilder()
	db_organize.levenshein_merger_groups(interactive=False, builder=builder)
	db_organize.release_merger_groups(interactive=False, builder=builder)

def flatten_history_table():
	with app.app_context():
		flatten_history.flatten_history()

def deduplicate_tags():
	with app.app_context():
		tag_manage.dedup_tags()
def deduplicate_genres():
	with app.app_context():
		tag_manage.dedup_genres()

def printer():
	print("Background task!")

tasks = [
	# (printer,                   "printer",                   15),
	(consolidate_rrl_items,        "consolidate_rrl_items",        hours( 1)),
	(flatten_series_by_url,        "flatten_series_by_url",        hours( 1)),
	(fix_escaped_quotes,           "fix_escaped_quotes",           hours( 1)),
	(clean_tags,                   "clean_tags",                   hours( 1)),
	(delete_bad_tags,              "delete_bad_tags",              hours( 1)),
	(delete_duplicate_releases,    "delete_duplicate_releases",    hours( 2)),
	(clean_garbage_releases,       "clean_garbage_releases",       hours( 1)),
	(trim_spaces,                  "trim_spaces",                  hours( 1)),
	(update_materialized_view,     "update_materialized_view",     hours( 1)),
	(update_to_merge_series_list,  "update_to_merge_series_list",  hours(48)),
	(update_to_merge_groups_list,  "update_to_merge_groups_list",  hours(48)),
	(flatten_history_table,        "flatten_history_table",        hours(48)),
	(deduplicate_tags,             "deduplicate_tags",             hours( 1)),
	(deduplicate_genres,           "deduplicate_genres",           hours( 1)),
]


def run_scheduler():
	print("Scheduler background thread running!")
	for task, taskname, taskinterval in tasks:
		job = scheduler.add_job(task, 'interval', id=taskname, seconds=taskinterval)
	print("Scheduler starting")
	scheduler.start()
	pass

def go():
	# delete_bad_tags()
	# update_materialized_view()
	# update_to_merge_groups_list()
	# update_to_merge_series_list()
	deduplicate_genres()

def go_all():

	consolidate_rrl_items()
	clean_garbage_releases()
	flatten_series_by_url()
	delete_duplicate_releases()
	fix_escaped_quotes()
	clean_tags()
	trim_spaces()
	update_materialized_view()
	update_to_merge_series_list()
	update_to_merge_groups_list()
	deduplicate_tags()

	delete_bad_tags()
	update_materialized_view()


def wat():
	update_to_merge_series_list()
	update_to_merge_groups_list()



if __name__ == "__main__":
	import logSetup
	import sys
	logSetup.initLogging()
	wat()


	# if "all" in sys.argv:
	# 	go_all()
	# else:
	# 	go()

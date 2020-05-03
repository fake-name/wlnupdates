#!flask/bin/python

# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from citext import CIText
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate
from flask_migrate import MigrateCommand

from app import app
from app import db
from app import models

import util.name_lookup
from util import tag_manage
from util import series_manage
import maintenance_scheduler

Migrate(app, db, compare_type=True)
manager = Manager(app)

# Unfortuntely, this couldn't be hooked into the `db upgrade` command, because it appears the changes to the DB
# are not accessible from the flask sqlalchemy context, even when python is exiting.
# I'm assuming it's because the changes are committed during exit, apparently.
@manager.command
def install_triggers():
	'''
	Install versioning triggers on tables
	'''
	print("Installing triggers")
	models.install_triggers()

# This is also true for my indexes, since they use postgres specific extensions.
@manager.command
def install_tgm_idx():
	'''
	Install trigram search indices on tables
	'''
	print("Installing trigram indices")
	models.install_trigram_indices()


@manager.command
def update_latest_meta():
	'''
	Update the 'latest vol/chp/frag' columns, as well as the last published column
	'''
	print("Updating latest chapter metadata")
	models.update_chp_info()


@manager.command
def resynchronize_ratings():
	'''
	Update the ratings aggregate from the discrete rating entry items.
	'''
	print("Updating latest chapter metadata")
	models.resynchronize_ratings()


@manager.command
def sync_counts():
	'''
	Update the chapter counts/latest/etc for each item.
	'''
	print("Updating latest chapter counts")
	models.resynchronize_latest_counts()


@manager.command
def recreate_mv():
	'''
	Destroy and recreate the materialized views.
	'''
	print("Recreating materialized viewsa")
	models.recreate_materialized_view()


# This is also true for my indexes, since they use postgres specific extensions.
@manager.command
def install_enum():
	'''
	Install enum type in db
	'''
	print("Installing enum indices")
	db.engine.begin()
	conn = db.engine.connect()
	models.install_region_enum(conn)
	models.install_tl_type_enum(conn)

	print("Done")

@manager.command
def validate_altnames():
	'''
	Check the altnames tables have valid entries for each item in the table they map to.
	'''
	print("Validating")
	models.validate_altnames()
	print("Done")

@manager.command
def fix_n_a_names():
	'''
	Remove all the entries of "N/A" in the altnames system (not sure where they're coming from).
	'''
	print("Cleaning")
	models.remove_n_a_altname()
	print("Done")

@manager.command
def fix_ampersands():
	'''
	Fix overencoded ampersands in the various content.
	'''
	print("Fixing")
	models.fix_ampersands()
	print("Done")


# This is also true for my indexes, since they use postgres specific extensions.
@manager.command
def do_name_lookup():
	'''
	Given a list of dotted names, look them up and return
	probable matches using the alt-names system
	'''

	util.name_lookup.do_search()

@manager.command
def find_similar_tags():
	'''
	Find tags within a small edit distance of each other
	'''
	print("Searching")
	with app.app_context():
		tag_manage.find_similar_tags()
	print("Done")

@manager.command
def apply_tag_lut():
	'''
	Apply the tag fix lookup table to ever series
	'''
	print("Fixing")
	with app.app_context():
		tag_manage.fix_from_tag_lut()
	print("Done")


@manager.command
def update_series_meta():
	'''
	Apply the tag fix lookup table to ever series
	'''
	print("Fixing")
	with app.app_context():
		series_manage.update_series_metadata_column()
	print("Done")





@manager.command
def consolidate_rrl_items():
	maintenance_scheduler.consolidate_rrl_items()

@manager.command
def flatten_series_by_url():
	maintenance_scheduler.flatten_series_by_url()

@manager.command
def fix_escaped_quotes():
	maintenance_scheduler.fix_escaped_quotes()

@manager.command
def clean_singleton_tags():
	maintenance_scheduler.clean_singleton_tags()

@manager.command
def delete_bad_tags():
	maintenance_scheduler.delete_bad_tags()

@manager.command
def delete_duplicate_releases():
	maintenance_scheduler.delete_duplicate_releases()

@manager.command
def clean_garbage_releases():
	maintenance_scheduler.clean_garbage_releases()

@manager.command
def trim_spaces():
	maintenance_scheduler.trim_spaces()

@manager.command
def update_materialized_view():
	maintenance_scheduler.update_materialized_view()

@manager.command
def update_to_merge_series_list():
	maintenance_scheduler.update_to_merge_series_list()

@manager.command
def update_to_merge_groups_list():
	maintenance_scheduler.update_to_merge_groups_list()

@manager.command
def flatten_history_table():
	maintenance_scheduler.flatten_history_table()

@manager.command
def deduplicate_tags():
	maintenance_scheduler.deduplicate_tags()

@manager.command
def deduplicate_genres():
	maintenance_scheduler.deduplicate_genres()

@manager.command
def consolidate_rrl_releases():
	maintenance_scheduler.consolidate_rrl_releases()


manager.add_command('db', MigrateCommand)



if __name__ == '__main__':
	print("Running migrator!")
	manager.run()


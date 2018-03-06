#!flask/bin/python

# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from app import app, db
from citext import CIText
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

import util.name_lookup
from app import models

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


# This is also true for my indexes, since they use postgres specific extensions.
@manager.command
def do_name_lookup():
	'''
	Given a list of dotted names, look them up and return
	probable matches using the alt-names system
	'''

	util.name_lookup.do_search()


manager.add_command('db', MigrateCommand)



if __name__ == '__main__':
	print("Running migrator!")
	manager.run()


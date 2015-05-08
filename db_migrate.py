#!flask/bin/python
from app import app, db
from citext import CIText
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from app import models
migrate = Migrate(app, db)
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



manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
	print("Running migrator!")
	manager.run()


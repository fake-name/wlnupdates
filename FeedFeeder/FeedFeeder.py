#!/usr/bin/env python3
from FeedFeeder.AmqpInterface import RabbitQueueHandler
import settings
import json
import datetime
from app import db
from app.models import Feeds, FeedAuthors, FeedTags


# user = Users(
# 	nickname  = form.username.data,
# 	password  = form.password.data,
# 	email     = form.email.data,
# 	verified  = 0
# )
# print("User:", user)
# db.session.add(user)
# db.session.commit()

# class Feeds(db.Model):

# 	id          = db.Column(db.Integer, primary_key=True)
# 	title       = db.Column(db.Text, nullable=False)
# 	contents    = db.Column(db.Text, nullable=False)
# 	guid        = db.Column(db.Text, unique=True)
# 	linkurl     = db.Column(db.Text, nullable=False)
# 	published   = db.Column(db.DateTime, index=True, nullable=False)
# 	updated     = db.Column(db.DateTime, index=True)
# 	region      = db.Column(region_enum, default='unknown')

# class FeedAuthors(db.Model):
# 	id          = db.Column(db.Integer, primary_key=True)
# 	article_id  = db.Column(db.Integer, db.ForeignKey('feeds.id'))
# 	name        = db.Column(CIText(), index=True, nullable=False)

# class FeedTags(db.Model):
# 	id          = db.Column(db.Integer, primary_key=True)
# 	article_id  = db.Column(db.Integer, db.ForeignKey('feeds.id'))
# 	tag         = db.Column(CIText(), index=True, nullable=False)



def insert_raw_item(item):
	'''
	insert item `item` into the feed database.

	fields in `item`:
		"title"
		"contents"
		"guid"
		"linkUrl"
		"feedtype"
		"published"
		"updated"

		"authors"
		->	"href"
		->	"name"
		"tags"

	'''

	# print(item)



	entry = {}
	entry['title']     = item.pop('title')
	entry['contents']  = item.pop('contents')
	entry['guid']      = item.pop('guid')
	entry['linkurl']   = item.pop('linkUrl')
	entry['region']    = item.pop('feedtype')
	entry['published'] = datetime.datetime.fromtimestamp(item.pop('published'))
	if 'updated' in item:
		entry['updated']   = datetime.datetime.fromtimestamp(item.pop('updated'))

	itemrow = Feeds.query.filter(Feeds.guid == entry['guid']).scalar()
	if not itemrow:
		print("New feed item: ", entry['guid'])
		itemrow = Feeds(**entry)
		db.session.add(itemrow)
		db.session.flush()




	for tag in item.pop('tags'):
		if not FeedTags.query                           \
			.filter(FeedTags.article_id==itemrow.id)    \
			.filter(FeedTags.tag == tag.strip()).scalar():

			newtag = FeedTags(article_id=itemrow.id, tag=tag.strip())
			db.session.add(newtag)
			db.session.flush()

	for author in item.pop('authors'):
		if not 'name' in author:
			continue

		if not FeedAuthors.query                        \
			.filter(FeedAuthors.article_id==itemrow.id) \
			.filter(FeedAuthors.name == author['name'].strip()).scalar():

			newtag = FeedAuthors(article_id=itemrow.id, name=author['name'].strip())
			db.session.add(newtag)
			db.session.flush()

	db.session.commit()

def dispatchItem(item):
	item = json.loads(item)
	assert 'type' in item
	assert 'data' in item

	if item['type'] == 'raw-feed':
		insert_raw_item(item['data'])
	elif item['type'] == 'parsed-release':
		print("Parsed release items not handled yet")
	else:
		print(item)
		raise ValueError("No known packet structure in item!")


class FeedFeeder(object):
	die = False

	def __init__(self):

		amqp_settings = {}
		amqp_settings["CLIENT_NAME"]        = settings.CLIENT_NAME
		amqp_settings["RABBIT_CLIENT_NAME"] = settings.RABBIT_CLIENT_NAME
		amqp_settings["RABBIT_LOGIN"]       = settings.RABBIT_LOGIN
		amqp_settings["RABBIT_PASWD"]       = settings.RABBIT_PASWD
		amqp_settings["RABBIT_SRVER"]       = settings.RABBIT_SRVER
		amqp_settings["RABBIT_VHOST"]       = settings.RABBIT_VHOST

		self.feeder = RabbitQueueHandler(settings=amqp_settings)

		print("Feed Feeder Initializing!")

	def process(self):
		while 1:
			data = self.feeder.get_item()
			if not data:
				break
			else:
				dispatchItem(data)

	def __del__(self):
		print("FeedFeeder being deleted")
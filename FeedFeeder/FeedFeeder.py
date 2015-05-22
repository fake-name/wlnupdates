#!/usr/bin/env python3
from FeedFeeder.AmqpInterface import RabbitQueueHandler
import settings
import json
import datetime
from app import db
from app.models import Feeds, FeedAuthors, FeedTags
from app.models import Translators, Releases, Series, AlternateNames, AlternateTranslatorNames
import traceback
import app.nameTools as nt
import time

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

# Hard coded RSS user ID. Probably a bad idea.
RSS_USER_ID = 3

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

	if not 'srcname' in item:
		print("No srcname? Old item?")
		return


	entry = {}
	entry['title']     = item.pop('title')
	entry['contents']  = item.pop('contents')
	entry['guid']      = item.pop('guid')
	entry['linkurl']   = item.pop('linkUrl')
	entry['region']    = item.pop('feedtype')
	entry['srcname']   = item.pop('srcname')
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

def get_create_group(groupname):
	have = Translators.query.filter(Translators.name==groupname).scalar()
	if not have:
		print("Need to create new translator entry for ", groupname)
		new = Translators(
				name = groupname,
				changeuser = RSS_USER_ID,
				changetime = datetime.datetime.now()
				)
		db.session.add(new)
		db.session.commit()
		newalt = AlternateTranslatorNames(
			group      = new.id,
			name       = new.name,
			cleanname  = nt.prepFilenameForMatching(new.name),
			changetime = datetime.datetime.now(),
			changeuser = RSS_USER_ID,
			)
		db.session.add(newalt)
		db.session.commit()
		return new
	return have

# {
# 	'series': 'I’m Back in the Other World?',
# 	'srcname': 'お兄ちゃん、やめてぇ！',
# 	'published': 1427995197.0,
# 	'chp': '9',
# 	'vol': None,
# 	'postfix': '',
# 	'itemurl': 'https://oniichanyamete.wordpress.com/2015/04/02/im-back-in-the-other-world-chapter-9/'
# }


def get_create_series(seriesname):
	have  = AlternateNames.query.filter(AlternateNames.name == seriesname).scalar()
	if not have:
		print("Need to create new series entry for ", seriesname)
		new = Series(
				title=seriesname,
				changeuser = RSS_USER_ID,  # Hard coded RSS user ID. Probably a bad idea.
				changetime = datetime.datetime.now(),

			)
		db.session.add(new)
		db.session.flush()


		newname = AlternateNames(
				name       = seriesname,
				cleanname  = nt.prepFilenameForMatching(seriesname),
				series     = new.id,
				changetime = datetime.datetime.now(),
				changeuser = RSS_USER_ID
			)
		db.session.add(newname)
		db.session.flush()
		db.session.commit()

		return new

	return have.series_row

def check_insert_release(item, group, series):
	have = Releases.query                            \
		.filter(Releases.series  == series.id)       \
		.filter(Releases.tlgroup == group.id)        \
		.filter(Releases.volume  == item['vol'])     \
		.filter(Releases.chapter == item['chp'])     \
		.filter(Releases.postfix == item['postfix']).all()
	if have:
		return
	print("Adding new release at date:", datetime.datetime.fromtimestamp(item['published']))
	release = Releases(
			series     = series.id,
			published  = datetime.datetime.fromtimestamp(item['published']),
			volume     = item['vol'],
			chapter    = item['chp'],
			include    = True,
			postfix    = item['postfix'],
			tlgroup    = group.id,
			changetime = datetime.datetime.now(),
			changeuser = RSS_USER_ID,
			srcurl     = item['itemurl'],
		)


	db.session.add(release)
	db.session.flush()
	db.session.commit()

def insert_parsed_release(item):

	group = get_create_group(item['srcname'])
	series = get_create_series(item['series'])

	# print(series)
	check_insert_release(item, group, series)


def dispatchItem(item):
	item = json.loads(item)
	assert 'type' in item
	assert 'data' in item

	if item['type'] == 'raw-feed':
		insert_raw_item(item['data'])
	elif item['type'] == 'parsed-release':
		insert_parsed_release(item['data'])
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
				try:
					dispatchItem(data)
				except Exception:
					with open("error - %s.txt" % time.time(), 'w') as fp:
						fp.write(traceback.format_exc())
					print("Error!")
					traceback.print_exc()

	def __del__(self):
		print("FeedFeeder being deleted")
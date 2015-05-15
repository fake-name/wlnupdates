#!/usr/bin/env python3
from FeedFeeder.AmqpInterface import RabbitQueueHandler
import settings

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
		print(self.feeder)

	def process(self):
		while 1:
			data = self.feeder.get_item()
			if not data:
				break
			else:
				print("Item:", len(data))

		print("Processing!")
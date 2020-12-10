#!/usr/bin/env python3
import msgpack
import settings
import datetime
import queue
from . import AmqpConnector
import logging
import threading
import os.path
import time
import ssl
import uuid


RUN_STATE = True

class RabbitQueueHandler(object):
	die = False

	def __init__(self, settings):

		logPath = 'Main.Feeds.RPC'

		self.log = logging.getLogger(logPath)
		print("RPC Management class instantiated.")


		# Require clientID in settings
		assert 'RABBIT_CLIENT_NAME' in settings
		assert "RABBIT_LOGIN"       in settings
		assert "RABBIT_PASWD"       in settings
		assert "RABBIT_SRVER"       in settings
		assert "RABBIT_VHOST"       in settings

		assert "CLIENT_NAME"        in settings



		sslopts = self.getSslOpts()

		self.connector = AmqpConnector.Connector(userid            = settings["RABBIT_LOGIN"],
												password           = settings["RABBIT_PASWD"],
												host               = settings["RABBIT_SRVER"],
												virtual_host       = settings["RABBIT_VHOST"],
												ssl                = sslopts,
												master             = False,
												synchronous        = False,
												flush_queues       = False,
												durable            = True,
												task_exchange_type = "fanout",
												task_queue         = 'task.{name}.q'.format(name=settings['CLIENT_NAME']),
												response_queue     = 'response.{name}.q'.format(name=settings['CLIENT_NAME']),
												poll_rate          = 0.001,
												prefetch           = 1000,

												# Allow the queue to be potentially lossy here.
												ack_rx             = False,
												)




	def getSslOpts(self):
		'''
		Verify the SSL cert exists in the proper place.
		'''
		curFile = os.path.abspath(__file__)

		curDir = os.path.split(curFile)[0]
		caCert = os.path.abspath(os.path.join(curDir, './cert/cacert.pem'))
		cert = os.path.abspath(os.path.join(curDir, './cert/cert.pem'))
		keyf = os.path.abspath(os.path.join(curDir, './cert/key.pem'))

		assert os.path.exists(caCert), "No certificates found on path '%s'" % caCert
		assert os.path.exists(cert), "No certificates found on path '%s'" % cert
		assert os.path.exists(keyf), "No certificates found on path '%s'" % keyf


		return {"cert_reqs" : ssl.CERT_REQUIRED,
				"ca_certs" : caCert,
				"keyfile"  : keyf,
				"certfile"  : cert,
			}

	def put_item(self, data):
		self.connector.putMessage(data)
		self.log.info("Outgoing data size: %s bytes.", len(data))


	def get_item(self):
		# print("GetItem call")
		ret = self.connector.getMessage()
		if ret:
			self.log.info("Processing %s byte message.", len(ret))
		# else:
		# 	self.log.info("No messages available.")

		return ret


	def __del__(self):
		self.close()

	def close(self):
		if self.connector:
			self.log.info("Non-null connector on shutdown. Halting interface")
			self.connector.stop()
			self.log.info("Connector stopped. Setting to null")
			self.connector = None









STATE = {}

def monitor(manager):
	while manager['amqp_runstate']:
		STATE['rpc_instance'].connector.checkLaunchThread()
		STATE['feed_instance'].connector.checkLaunchThread()
		time.sleep(1)
		print("Monitor looping!")


def startup_interface(manager):
	rpc_amqp_settings = {
		'RABBIT_LOGIN'    : settings.RPC_RABBIT_LOGIN,
		'RABBIT_PASWD'    : settings.RPC_RABBIT_PASWD,
		'RABBIT_SRVER'    : settings.RPC_RABBIT_SRVER,
		'RABBIT_VHOST'    : settings.RPC_RABBIT_VHOST,
		'master'          : True,
		'prefetch'        : 250,
		# 'prefetch'        : 50,
		# 'prefetch'        : 5,
		'queue_mode'      : 'direct',
		'taskq_task'      : 'task.q',
		'taskq_response'  : 'response.q',

		"poll_rate"       : 1/100,

		'taskq_name' : 'outq',
		'respq_name' : 'inq',

	}

	feed_amqp_settings = {
		'RABBIT_LOGIN'    : settings.RABBIT_LOGIN,
		'RABBIT_PASWD'    : settings.RABBIT_PASWD,
		'RABBIT_SRVER'    : settings.RABBIT_SRVER,
		'RABBIT_VHOST'    : settings.RABBIT_VHOST,
		'master'          : True,
		'prefetch'        : 25,
		# 'prefetch'        : 50,
		# 'prefetch'        : 5,
		'queue_mode'              : 'fanout',
		'taskq_task'              : 'task.q',
		'taskq_response'          : 'response.q',

		'task_exchange_type'      : 'fanout',
		'response_exchange_type'  : 'direct',


		"poll_rate"               : 1/100,

		'taskq_name'              : 'feed_outq',
		'respq_name'              : 'feed_inq',
	}

	STATE['rpc_instance'] = RabbitQueueHandler(rpc_amqp_settings, manager)
	STATE['rpc_thread'] = threading.Thread(target=STATE['rpc_instance'].runner)
	STATE['rpc_thread'].start()

	STATE['feed_instance'] = PlainRabbitQueueHandler(feed_amqp_settings, manager)
	STATE['feed_thread'] = threading.Thread(target=STATE['feed_instance'].runner)
	STATE['feed_thread'].start()

	STATE['monitor_thread'] = threading.Thread(target=monitor, args=[manager])
	STATE['monitor_thread'].start()


def shutdown_interface(manager):
	print("Halting AMQP interface")
	manager['amqp_runstate'] = False
	STATE['rpc_thread'].join()
	STATE['feed_thread'].join()
	STATE['monitor_thread'].join()


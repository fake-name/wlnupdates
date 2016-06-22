#!/usr/bin/env python3
import AmqpConnector
import logging
import os.path
import ssl

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
												poll_rate          = 0.010,
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
			self.log.info("Received data size: %s bytes.", len(ret))
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



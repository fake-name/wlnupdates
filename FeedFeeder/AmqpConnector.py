
import amqpstorm
import urllib.parse
import socket
import random
import traceback
import logging
import threading
import multiprocessing
import queue
import time



class Heartbeat_Timeout_Exception(Exception):
	pass

class Message_Publish_Exception(Exception):
	pass

class ConnectorManager:
	def __init__(self, config, runstate, task_queue, response_queue):

		assert 'host'                     in config
		assert 'userid'                   in config
		assert 'password'                 in config
		assert 'virtual_host'             in config
		assert 'task_queue_name'          in config
		assert 'response_queue_name'      in config
		assert 'task_exchange'            in config
		assert 'task_exchange_type'       in config
		assert 'response_exchange'        in config
		assert 'response_exchange_type'   in config
		assert 'master'                   in config
		assert 'synchronous'              in config
		assert 'flush_queues'             in config
		assert 'heartbeat'                in config
		assert 'sslopts'                  in config
		assert 'poll_rate'                in config
		assert 'prefetch'                 in config
		assert 'durable'                  in config
		assert 'socket_timeout'           in config
		assert 'hearbeat_packet_timeout'  in config
		assert 'ack_rx'                   in config

		self.is_master = config['master']

		self.log = logging.getLogger("Main.Connector.Internal(%s)" % config['virtual_host'])
		self.runstate           = runstate
		self.config             = config
		self.task_queue         = task_queue
		self.response_queue     = response_queue

		self.connected          = multiprocessing.Value("i", 0)

		self.had_exception      = multiprocessing.Value("i", 0)
		self.threads_live       = multiprocessing.Value("i", 1)

		self.thread_management_lock = threading.Lock()


		self.info_printerval        = time.time()
		self.last_hearbeat_sent     = time.time()
		self.last_hearbeat_received = time.time()
		self.last_message_received  = time.time()

		self.rx_timeout_lock        = threading.Lock()
		self.heartbeat_timeout_lock = threading.Lock()


		self.session_fetched        = 0
		self.queue_fetched          = 0
		self.active                 = 0
		self.sent_messages = 0
		self.recv_messages = 0

		self.keepalive_num     = 0
		self.prefetch_extended = False

		self.delivered = 0
		self.die_timeout = time.time()

		self.connect_lock = threading.Lock()
		self.__connect()

	def __connect(self):


		self.hearbeat_packet_timeout = self.config['hearbeat_packet_timeout']
		self.keepalive_exchange_name = "keepalive_exchange"+str(id("wat"))

		self.__open_connection()
		self.__reset_channel()


	def __open_connection(self):
		self.log.info("Initializing AMQP connection.")
		self.storm_connection = amqpstorm.Connection(
				hostname     = self.config['host'].split(":")[0],
				username     = self.config['userid'],
				password     = self.config['password'],
				port         = int(self.config['host'].split(":")[1]),
				virtual_host = self.config['virtual_host'],
				heartbeat    = self.config['socket_timeout'] // 2,
				timeout      = self.config['socket_timeout'],
				ssl          = True,
				ssl_options  = {
					'ca_certs'           : self.config['sslopts']['ca_certs'],
					'certfile'           : self.config['sslopts']['certfile'],
					'keyfile'            : self.config['sslopts']['keyfile'],
				}

			)


	def __reset_channel(self):

		if hasattr(self, 'storm_channel'):
			close_funcs = [
				self.storm_channel.stop_consuming,
				self.storm_channel.close,
			]
			for cfunc in close_funcs:
				try:
					cfunc()
				except Exception as e:
					self.log.warning("Warning when tearing down connection!")
					for line in traceback.format_exc().split("\n"):
						self.log.warning(line)

		self.__configure_channel()
		self.__configure_rpc_exchanges()
		self.__configure_keepalive_channel()

		# Re-enqueue any not-acked packets.
		self.storm_channel.basic.recover(requeue=True)
		self.storm_channel._inbound.clear()

		self.__start_consume()

	def __configure_channel(self):

		self.log.info("Connection established. Setting up consumer.")
		self.storm_channel = self.storm_connection.channel(rpc_timeout=self.config['socket_timeout'])

		# Initial QoS is tiny, throttle it up after everything is actually running.
		self.storm_channel.basic.qos(1, global_=True)
		self.prefetch_extended = False

	def __configure_keepalive_channel(self):

		# "NAK" queue, used for keeping the event loop ticking when we
		# purposefully do not want to receive messages
		# THIS IS A SHITTY WORKAROUND for keepalive issues.

		self.log.info("Configuring keepalive channel")
		self.storm_channel.exchange.declare(
					exchange=self.keepalive_exchange_name,
					durable=False,
					auto_delete=True)

		self.storm_channel.queue.declare(
					queue=self.keepalive_exchange_name+'.nak.q',
					durable=False,
					auto_delete=True)

		self.storm_channel.queue.bind(
					queue=self.keepalive_exchange_name+'.nak.q',
					exchange=self.keepalive_exchange_name,
					routing_key="nak")

		self.log.info("Configuring keepalive channel complete")

	def __configure_rpc_exchanges(self):

		self.log.info("Configuring RPC channel.")

		# self.is_master

		self.log.info("Declaring task exchange: '%s' -> '%s' -> '%s'", self.config['task_exchange'], self.config['task_exchange_type'], self.config['durable'])
		self.storm_channel.exchange.declare(
					exchange      = self.config['task_exchange'],
					exchange_type = self.config['task_exchange_type'],
					durable       = self.config['durable']
				)

		self.log.info("Declaring response exchange: '%s' -> '%s' -> '%s'", self.config['response_exchange'], self.config['response_exchange_type'], self.config['durable'])
		self.storm_channel.exchange.declare(
					exchange      =self.config['response_exchange'],
					exchange_type =self.config['response_exchange_type'],
					durable       =self.config['durable']
				)


		# # set up consumer and response queues
		# if self.config['master']:
		# 	# Master has to declare the response queue so it can listen for responses
		# 	self.channel.queue_declare(self.config['response_queue_name'], auto_delete=False, durable=self.config['durable'])
		# 	self.channel.queue_bind(   self.config['response_queue_name'], exchange=self.config['response_exchange'], routing_key=self.config['response_queue_name'].split(".")[0])
		# 	self.log.info("Binding queue %s to exchange %s.", self.config['response_queue_name'], self.config['response_exchange'])

		# if not self.config['master']:
		# 	# Clients need to declare their task queues, so the master can publish into them.
		# 	self.channel.queue_declare(self.config['task_queue_name'], auto_delete=False, durable=self.config['durable'])
		# 	self.channel.queue_bind(   self.config['task_queue_name'], exchange=self.config['task_exchange'], routing_key=self.config['task_queue_name'].split(".")[0])
		# 	self.log.info("Binding queue %s to exchange %s.", self.config['task_queue_name'], self.config['task_exchange'])


		self.log.info("Declaring response queue: '%s' -> '%s'", self.config['response_queue_name'], self.config['durable'])
		self.storm_channel.queue.declare(
					queue         =self.config['response_queue_name'],
					durable       =self.config['durable'],
					auto_delete=False)

		self.log.info("Binding queue '%s' to '%s' with routing key '%s'", self.config['response_queue_name'], self.config['response_exchange'], self.config['response_queue_name'].split(".")[0])
		self.storm_channel.queue.bind(
					queue         =self.config['response_queue_name'],
					exchange      =self.config['response_exchange'],
					routing_key   =self.config['response_queue_name'].split(".")[0])

		self.log.info("Configured.")


	def __poke_keepalive(self):
		mbody = "keepalive %s, random: %s" % (self.keepalive_num, random.random())
		self.storm_channel.basic.publish(body=mbody, exchange=self.keepalive_exchange_name, routing_key='nak',
			properties={
				'correlation_id' : "keepalive_{}".format(self.keepalive_num)
			})
		self.keepalive_num += 1
		self.last_hearbeat_sent = time.time()



	def __do_rx(self):
		self.storm_channel.process_data_events(to_tuple=False, auto_decode=False)

	def handle_rx(self, message):
		# self.log.info("Received message!")
		# self.log.info("Message channel: %s", message.channel)
		# self.log.info("Message properties: %s", message.properties)
		corr_id = message.properties['correlation_id']
		if isinstance(corr_id, (bytes, bytearray)):
			corr_id = corr_id.decode('ascii')
		if corr_id.startswith('keepalive'):
			self.__handle_keepalive_rx(corr_id, message)
		else:
			self.__handle_normal_rx(corr_id, message)

		if self.prefetch_extended is False:
			self.prefetch_extended = True
			self.storm_channel.basic.qos(1000, global_=True)
			self.log.info("Prefetch updated")



	def __handle_keepalive_rx(self, corr_id, message):

		with self.heartbeat_timeout_lock:
			self.last_hearbeat_received = time.time()
		message.ack()
		self.log.info("Heartbeat packet received! %s -> %s", message.body.decode("ascii"), corr_id)

	def __handle_normal_rx(self, corr_id, message):

		with self.rx_timeout_lock:
			self.last_message_received = time.time()

		count = 0
		while self.response_queue.qsize() > 500:
			time.sleep(0.1)
			count += 1
			if count > 100:
				self.log.info("AMQP Connector sleeping while queue is processed.")

		self.response_queue.put(message.body)
		message.ack()

		self.log.info("Message packet received: %s. Queue size: %s", len(message.body), self.response_queue.qsize())


	def __start_consume(self):
		self.log.info("Bound. Triggering consume")
		self.storm_channel.basic.consume(self.handle_rx, queue=self.config['response_queue_name'],    no_ack=False)
		self.storm_channel.basic.consume(self.handle_rx, queue=self.keepalive_exchange_name+'.nak.q', no_ack=False)
		self.log.info("Consume triggered.")


	def __do_tx(self):

		for dummy_x in range(500):

			if self.__should_die():
				self.log.info("Transmit loop saw exit flag. Breaking!")
				return
			# self.log.info("Items in outgoing TX queue: %s", self.task_queue.qsize())
			print("/", end="", flush=True)
			try:
				put = self.task_queue.get_nowait()
			except queue.Empty:
				return

			try:

				# print("Putting item: ", put, self.config['task_exchange'], self.config)

				out_key   = self.config['task_queue_name'].split(".")[0]

				msg_prop = {}
				if self.config['task_queue_name']:
					msg_prop["delivery_mode"] = 2

				if not self.storm_channel:
					raise Message_Publish_Exception("Failed to publish message!")

				self.storm_channel.basic.publish(body=put, exchange=self.config['task_exchange'], routing_key=out_key, properties=msg_prop)

				self.sent_messages += 1
				self.active -= 1

			except amqpstorm.AMQPError as e:
				self.log.error("Error while tx_polling interface!")
				self.task_queue.put(put)
				self.log.error("	%s", e)
				for line in traceback.format_exc().split("\n"):
					self.log.error(line)
				self.had_exception.value = 1
				return
			except Message_Publish_Exception as e:
				self.log.error("Error while publishing message!")
				self.task_queue.put(put)
				self.log.error("	%s", e)
				for line in traceback.format_exc().split("\n"):
					self.log.error(line)
				self.had_exception.value = 1
				return



	def __should_die(self):
		# ret = self.runstate.value != 1 or self.threads_live.value != 1 or self.had_exception.value != 0

		if self.runstate.value == 1:
			self.die_timeout = time.time()
		elif self.response_queue.qsize() > 0:
			pass
		else:
			self.die_timeout -= 500

		ret = self.threads_live.value != 1 or self.had_exception.value != 0 or (time.time() - self.die_timeout > 20)
		if ret:

			self.log.warning("Should die flag! Runstate: %s, threads live: %s, had exception: %s.",
				"running" if self.runstate.value == 1 else "halting",
				"threads alive" if self.threads_live.value == 1 else "threads stopping",
				"yes" if self.had_exception.value == 1 else "no"
				)
		return ret


	def __check_timeouts(self):
		now = time.time()

		if self.info_printerval + 10 < now:
			self.log.info("Interface timeout thread. Ages: heartbeat -> %0.2f, last message -> %0.2f, TX, RX q: (%s, %s).",
					now - self.last_hearbeat_received,
					now - self.last_message_received,
					self.task_queue.qsize(),
					self.response_queue.qsize(),
					)
			self.info_printerval += 10

		# Send heartbeats every 5 seconds.
		if self.last_hearbeat_sent + 5 < now:
			self.__poke_keepalive()

		if self.last_hearbeat_received + self.config['hearbeat_packet_timeout'] < now:
			self.log.error("Heartbeat receive timeout! Triggering reconnect due to missed heartbeat.")
			self.last_hearbeat_received = now
			try:
				self.__reset_channel()
			except:
				self.had_exception.value = 1


		if (self.last_message_received + (self.config['hearbeat_packet_timeout'] * 100) < now or
			self.last_hearbeat_received + (self.config['hearbeat_packet_timeout'] * 100) < now):
			# Attempt recover if we've been idle for a while.
			self.log.info("Reconnect retrigger seems to have not fixed the issue (or just no messages)?")

			self.had_exception.value = 1


	def run(self):

		self.__start_consume()
		while not self.__should_die():
			try:
				print("\\", end="", flush=True)
				self.__do_tx()
				self.__do_rx()
				self.__check_timeouts()
				time.sleep(0.1)
			except Exception as e:
				with open("mq error %s.txt" % time.time(), 'w') as fp:
					fp.write("Error!\n\n")
					fp.write(traceback.format_exc())
				self.log.error("Error!")
				self.log.error("%s", e)
				for line in traceback.format_exc().split("\n"):
					self.log.error(line)
				raise e



	def disconnect(self):
		with self.connect_lock:
			self.prefetch_extended = False
			self.threads_live.value = 0
			self.storm_channel.close()
			self.storm_connection.close()


	def shutdown(self):
		self.log.info("ConnectorManager shutdown called!")
		for dummy_x in range(30):
			qs = self.task_queue.qsize()
			if qs == 0:
				break
			else:
				self.log.warning("Outgoing queue draining. Items: %s", qs)
				self.__do_tx()
				time.sleep(1)
		self.threads_live.value = 0
		self.disconnect()

	def __del__(self):
		self.shutdown()

	@classmethod
	def run_fetcher(cls, config, runstate, tx_q, rx_q):
		'''
		bleh

		'''

		log = logging.getLogger("Main.Connector.Manager(%s)" % config['virtual_host'])

		log.info("Worker thread starting up.")
		try:
			print("Connecting %s" % config['virtual_host'])
			interface = cls(config, runstate, tx_q, rx_q)
			print("Entering monitor-loop %s, runstate: %s" % (config['virtual_host'], runstate.value))
			interface.run()

		except Exception:
			log.error("Exception in connector! Terminating connection...")
			for line in traceback.format_exc().split('\n'):
				log.error(line)

			if runstate.value != 0:
				log.error("Triggering reconnection...")

		try:
			interface.shutdown()
		except Exception:
			log.info("")
			log.error("Failed pre-emptive closing before reconnection. May not be a problem?")
			for line in traceback.format_exc().split('\n'):
				log.error(line)

		log.info("")
		log.info("Worker thread has terminated.")
		log.info("")

class Connector:

	def __init__(self, *args, **kwargs):

		assert args == (), "All arguments must be passed as keyword arguments. Positional arguments: '%s'" % (args, )

		self.log = logging.getLogger("Main.Connector")
		self.thread_management_lock = threading.Lock()

		self.log.info("Setting up AqmpConnector!")

		config = {
			'host'                     : kwargs['host'],
			'userid'                   : kwargs['userid'],
			'password'                 : kwargs['password'],
			'virtual_host'             : kwargs['virtual_host'],
			'task_queue_name'          : kwargs['task_queue'],
			'response_queue_name'      : kwargs['response_queue'],
			'task_exchange_type'       : kwargs['task_exchange_type'],
			'task_exchange'            : kwargs.get('task_exchange',            'tasks.e'),
			'response_exchange'        : kwargs.get('response_exchange',        'resps.e'),
			'response_exchange_type'   : kwargs.get('response_exchange_type',   'direct'),
			'master'                   : kwargs.get('master',                   False),
			'synchronous'              : kwargs.get('synchronous',              True),
			'flush_queues'             : kwargs.get('flush_queues',             False),
			'heartbeat'                : kwargs.get('heartbeat',                 15),
			'sslopts'                  : kwargs.get('ssl',                      None),
			'poll_rate'                : kwargs.get('poll_rate',                  0.25),
			'prefetch'                 : kwargs.get('prefetch',                   1),
			'durable'                  : kwargs.get('durable',                  False),
			'socket_timeout'           : kwargs.get('socket_timeout',            15),

			'hearbeat_packet_timeout'  : kwargs.get('hearbeat_packet_timeout',  30),
			'ack_rx'                   : kwargs.get('ack_rx',                   True),
		}

		assert config['hearbeat_packet_timeout'] > config['socket_timeout'],                                   \
			"Heartbeat time must be greater then socket timeout! Heartbeat interval: %s. Socket timeout: %s" % \
			(config['hearbeat_packet_timeout'], config['socket_timeout'])

		self.log.info("Using virtualhost: '%s'.", config['virtual_host'])
		self.log.info("Comsuming from queue '%s', emitting responses on '%s'.", config['task_queue_name'], config['response_queue_name'])

		# Validity-Check args
		if not config['host']:
			raise ValueError("You must specify a host to connect to!")

		assert        config['task_queue_name'].endswith(".q") is True
		assert    config['response_queue_name'].endswith(".q") is True
		assert     config['task_exchange'].endswith(".e") is True
		assert config['response_exchange'].endswith(".e") is True

		self.is_master = config['master']

		# If we're not the master, swap the queues.
		if not self.is_master:
			config['task_queue_name'], config['response_queue_name']       = config['response_queue_name'], config['task_queue_name']
			config['task_exchange'], config['response_exchange']           = config['response_exchange'], config['task_exchange']
			config['task_exchange_type'], config['response_exchange_type'] = config['response_exchange_type'], config['task_exchange_type']

		# Patch in the port number to the host name if it's not present.
		# This is really clumsy, but you can't explicitly specify the port
		# in the amqp library
		if not ":" in config['host']:
			if config['ssl']:
				config['host'] += ":5671"
			else:
				config['host'] += ":5672"


		self.queue_fetched       = 0
		self.queue_put           = 0

		# set up the task and response queues.
		# These need to be multiprocessing queues because
		# messages can sometimes be inserted from a different process
		# then the interface is created in.
		self.taskQueue = queue.Queue()
		self.responseQueue = queue.Queue()

		self.runstate = multiprocessing.Value("b", 1)

		self.log.info("Starting AMQP interface thread.")

		self.forwarded = 0

		with self.thread_management_lock:
			self.thread = None
		self.__config = config
		self.checkLaunchThread()

	def checkLaunchThread(self):
		queue_overfull = self.taskQueue.qsize() > 10000

		with self.thread_management_lock:
			if self.thread and self.thread.isAlive() and not queue_overfull:
				return
		if queue_overfull:
			self.runstate.value = 0
			for dummy_x in range(30):

				with self.thread_management_lock:
					if not self.thread.isAlive():
						self.thread.join()
						self.thread = None
						break
				time.sleep(1)


		with self.thread_management_lock:

			if self.thread and not self.thread.isAlive():
				self.thread.join()
				self.log.error("")
				self.log.error("")
				self.log.error("")
				self.log.error("Thread has died!")
				self.log.error("")
				self.log.error("")
				self.log.error("")

			self.thread = threading.Thread(
				target=ConnectorManager.run_fetcher,
				args=(self.__config, self.runstate, self.taskQueue, self.responseQueue),
				daemon=True,
				name="RMQ: {}".format(self.__config['virtual_host']))

			self.thread.start()
			while not self.thread.isAlive():
				time.sleep(1)
				self.log.info("Waiting for thread to start")




	def getMessage(self):
		'''
		Try to fetch a message from the receiving Queue.
		Returns the method if there is one, False if there is not.
		Non-Blocking.
		'''
		self.checkLaunchThread()

		try:
			put = self.responseQueue.get_nowait()
			self.queue_fetched += 1
			self.forwarded += 1
			if self.forwarded >= 25:
				self.log.info("Fetched item from proxy queue. Total received: %s, total sent: %s, qsizes: %s, %s", self.queue_fetched, self.queue_put, self.responseQueue.qsize(), self.taskQueue.qsize())
				self.forwarded = 0
			return put
		except queue.Empty:
			return None

	def putMessage(self, message, synchronous=False):
		'''
		Place a message into the outgoing queue.

		the items in the outgoing queue are less then the
		value of synchronous
		'''
		self.checkLaunchThread()
		timeouts = 0
		if synchronous:
			while self.taskQueue.qsize() > synchronous:
				time.sleep(0.1)
				timeouts += 1
				if timeouts > 100:
					return self.taskQueue.qsize()
		self.queue_put += 1
		self.taskQueue.put(message)

		return self.taskQueue.qsize()


	def stop(self):
		'''
		Tell the AMQP interface thread to halt, and then join() on it.
		Will block until the queue has been cleanly shut down.
		'''
		self.log.info("Stopping AMQP interface thread.")
		self.runstate.value = 0
		if self.is_master:
			resp_q = self.responseQueue
		else:
			resp_q = self.taskQueue

		block = 0
		blocklen = 25
		while resp_q.qsize() > 0:
			self.log.info("%s remaining outgoing AMQP items (%s).", resp_q.qsize(), blocklen-block)
			time.sleep(1)
			block += 1
			if block > blocklen:
				break

		self.log.info("%s remaining outgoing AMQP items. Joining on thread.", resp_q.qsize())


		with self.thread_management_lock:
			self.thread.join()

		self.log.info("AMQP interface thread halted.")

	def __del__(self):
		# print("deleter: ", self.runstate, self.runstate.value)
		if self.runstate.value:
			self.stop()



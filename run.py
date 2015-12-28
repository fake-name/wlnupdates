#!flask/bin/python
try:
	import logSetup
	logSetup.initLogging()
except:
	print("No logging!")
	import traceback
	traceback.print_exc()
	pass

from app import app
import threading
import time
import calendar

import FeedFeeder.FeedFeeder
import flags

def thread_run():
	interface = None
	while flags.RUNSTATE:
		try:
			if not interface:
				interface = FeedFeeder.FeedFeeder.FeedFeeder()
			interface.process()
		except Exception:
			interface = None
			time.sleep(60)
		time.sleep(1)
	print("Background thread closing interface")
	if interface:
		interface.close()


def startBackgroundThread():
	print("ThreadStarter")

	bk_thread = threading.Thread(target = thread_run)
	bk_thread.start()
	return bk_thread


def go():
	import sys

	if not "debug" in sys.argv:
		print("Starting background thread")
		bk_thread = startBackgroundThread()

	if "debug" in sys.argv:
		from gevent.pywsgi import WSGIServer

		print("Running in debug mode.")
		app.run(host='0.0.0.0')
	else:

		import cherrypy
		import logging


		def fixup_cherrypy_logs():
			loggers = logging.Logger.manager.loggerDict.keys()
			for name in loggers:
				if name.startswith('cherrypy.'):
					print("Fixing %s." % name)
					logging.getLogger(name).propagate = 0


		cherrypy.tree.graft(app, "/")
		cherrypy.server.unsubscribe()

		# Instantiate a new server object
		server = cherrypy._cpserver.Server()
		# Configure the server object
		if "all" in sys.argv:
			server.socket_host = "0.0.0.0"
		else:
			server.socket_host = "127.0.0.1"

		server.socket_port = 5000
		server.thread_pool = 8

		# For SSL Support
		# server.ssl_module            = 'pyopenssl'
		# server.ssl_certificate       = 'ssl/certificate.crt'
		# server.ssl_private_key       = 'ssl/private.key'
		# server.ssl_certificate_chain = 'ssl/bundle.crt'

		# Subscribe this server
		server.subscribe()

		# fixup_cherrypy_logs()

		if hasattr(cherrypy.engine, 'signal_handler'):
			cherrypy.engine.signal_handler.subscribe()
		# Start the server engine (Option 1 *and* 2)
		cherrypy.engine.start()
		cherrypy.engine.block()
		# fixup_cherrypy_logs()



	print()
	print("Interrupt!")
	if not "debug" in sys.argv:
		print("Joining on background thread")
		flags.RUNSTATE = False
		bk_thread.join()

	print("Thread halted. App exiting.")

if __name__ == "__main__":
	started = False
	if not started:
		started = True
		go()

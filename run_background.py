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
import maintenance_scheduler

import FeedFeeder.FeedFeeder
import flags

def amqp_thread_run():
	print("AMQP Thread running.")
	interface = None
	while flags.RUNSTATE:
		try:
			if not interface:
				interface = FeedFeeder.FeedFeeder.FeedFeeder()
			interface.process()
		except Exception:
			interface = None
			time.sleep(10)
		time.sleep(1)
	print("Background thread closing interface")
	if interface:
		interface.close()


def startBackgroundThreads():
	print("ThreadStarter")

	amqp_bk_thread = threading.Thread(target = amqp_thread_run)
	amqp_bk_thread.start()

	scheduler_bk_thread = threading.Thread(target = maintenance_scheduler.run_scheduler)
	scheduler_bk_thread.start()
	return [amqp_bk_thread, scheduler_bk_thread]


def go():

	bk_threads = startBackgroundThreads()

	try:
		while True:
			time.sleep(10)
	except KeyError:
		pass


	print("Joining on background thread")
	flags.RUNSTATE = False
	for bk_thread in bk_threads:
		bk_thread.join()

	print("Thread halted. App exiting.")

if __name__ == "__main__":
	started = False
	if not started:
		started = True
		go()

#!flask/bin/python
try:
	import logSetup
	logSetup.initLogging()
except:
	print("No logging!")
	import traceback
	traceback.print_exc()
	pass


import sys

from app import app
import threading
import concurrent.futures
import time
import maintenance_scheduler

import FeedFeeder.FeedFeeder
import flags


def amqp_thread_run(silence_exceptions=True):
	print("AMQP Thread running.")
	interface = None

	# This nesting makes me sad, but I don't want to have threads continually
	# being created/destroyed.
	while flags.RUNSTATE:
		try:
			workers = 3
			with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as exc:
				while flags.RUNSTATE:
					if not interface:
						interface = FeedFeeder.FeedFeeder.FeedFeeder()

					res = [exc.submit(interface.process) for _ in range(workers * 10)]
					[item.result() for item in res]

		except KeyboardInterrupt:
			break

		except Exception:
			if silence_exceptions:
				with open("threading error %s.txt" % time.time(), 'w') as fp:
					fp.write("Error!\n\n")
					fp.write(traceback.format_exc())
				traceback.print_exc()
				interface = None
				time.sleep(10)
			else:
				raise


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


def go_old():

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


def go():

	if "feeder" in sys.argv:
		amqp_thread_run(silence_exceptions=False)
	elif "scheduler" in sys.argv:
		maintenance_scheduler.run_scheduler()
	else:
		raise RuntimeError("Invalid run mode!")




if __name__ == "__main__":
	started = False
	if not started:
		started = True
		go()

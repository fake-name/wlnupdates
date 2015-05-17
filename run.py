#!flask/bin/python

from app import app
import threading
import time
import calendar

import FeedFeeder.FeedFeeder
import flags

def thread_run():
	interface = FeedFeeder.FeedFeeder.FeedFeeder()
	while flags.RUNSTATE:
		interface.process()
		time.sleep(1)


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
		print("Running in debug mode.")
		app.run(host='0.0.0.0')
	elif "all" in sys.argv:
		print("Running in all IP mode.")
		app.run(host='0.0.0.0')
	else:
		print("Running in normal mode.")
		app.run()

	# print()
	# print("Interrupt!")
	# print("Joining on background thread")

	if not "debug" in sys.argv:
		flags.RUNSTATE = False
		bk_thread.join()

	# print("Thread halted. App exiting.")

if __name__ == "__main__":
	started = False
	if not started:
		started = True
		go()

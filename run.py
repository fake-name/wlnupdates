#!flask/bin/python

from app import app
import threading
import time

import FeedFeeder.FeedFeeder

RUNSTATE = True

def thread_run():
	interface = FeedFeeder.FeedFeeder.FeedFeeder()
	while RUNSTATE:
		print("Thread!")
		interface.process()
		time.sleep(1)

	print("Thread received halt signal. Exiting.")

def startBackgroundThread():
	thread = threading.Thread(target = thread_run)
	thread.start()

	return thread


def go():
	import sys

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

	print()
	print("Interrupt!")
	print("Joining on background thread")

	global RUNSTATE
	RUNSTATE = False
	bk_thread.join()

	print("Thread halted. App exiting.")

if __name__ == "__main__":
	go()

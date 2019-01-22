

print("Utilities Startup")


import logSetup
logSetup.initLogging()

import signal
import sys
import os.path

from app import app
from app import api_handlers_admin
import util.db_organize
import util.flatten_history

def printHelp():

	print("################################### ")
	print("##   System maintenance script   ## ")
	print("################################### ")
	print("")
	print("*********************************************************")
	print("Organizing Tools")
	print("*********************************************************")
	print("	flatten-series-by-url")
	print("		")
	print("	delete-duplicate-releases")
	print("		")
	print("	fix-escaped-quotes")
	print("		")
	print("	clean-singleton-tags")
	print("		")
	print("	delete-postfix")
	print("		")
	print("	lv-merge-series")
	print("		Use levenshtein string distance metrics to try to heuristically automatically")
	print("		merge series with multiple instances.")
	print("		")
	print("		")
	print("	minhash-merge-series")
	print("		Use minhash string distance metrics to try to heuristically automatically")
	print("		merge series with multiple instances.")
	print("		")
	print("	lv-auto-calc")
	print("		Use levenshtein string distance metrics to try to heuristically automatically")
	print("		merge series with multiple instances, write result to file for web-ui rather")
	print("		then user-interactive merging.")
	print("		")
	print("	flatten-history")
	print("		Find and consolidate change entries that don't actually have changes..")
	print()
	return


one_arg_map = {

}


def parseOneArgCall(cmd):


	mainArg = sys.argv[1]

	print ("Passed arg", mainArg)


	arg = mainArg.lower()


	if arg == "flatten-series-by-url":
		with app.app_context():
			print(api_handlers_admin.flatten_series_by_url(None, admin_override=True))
	elif arg == "delete-duplicate-releases":
		with app.app_context():
			print(api_handlers_admin.delete_duplicate_releases(None, admin_override=True))
	elif arg == "fix-escaped-quotes":
		with app.app_context():
			print(api_handlers_admin.fix_escaped_quotes(None, admin_override=True))
	elif arg == "clean-singleton-tags":
		with app.app_context():
			print(api_handlers_admin.clean_singleton_tags(None, admin_override=True))
	elif arg == "delete-postfix":
		with app.app_context():
			util.db_organize.delete_postfix()
	elif arg == "lv-merge-series":
		util.db_organize.levenshein_merger_series()
	elif arg == "minhash-merge-series":
		util.db_organize.minhash_merger_series()
	elif arg == "lv-auto-calc":
		util.db_organize.levenshein_merger_series(interactive=False)
	elif arg == "lv-group-calc":
		util.db_organize.levenshein_merger_groups(interactive=False)
	elif arg == "flatten-history":
		util.flatten_history.flatten_history()
	else:
		print("Unknown arg!")


def parseTwoArgCall(cmd, val):
	if cmd == "import":
		# if not os.path.exists(val):
		# 	print("Passed path '%s' does not exist!" % val)
		# 	return
		# autoImporter.importDirectories(val)
		return

	else:
		print("Did not understand command!")
		print("Sys.argv = ", sys.argv)

def parseThreeArgCall(cmd, arg1, arg2):
	if cmd == "dirs-clean":
		# if not os.path.exists(arg1):
		# 	print("Passed path '%s' does not exist!" % arg1)
		# 	return
		# elif not os.path.exists(arg2):
		# 	print("Passed path '%s' does not exist!" % arg2)
		# 	return
		# utilities.dedupDir.runDeduper(arg1, arg2)
		return

	else:
		print("Did not understand command!")
		print("Sys.argv = ", sys.argv)

def parseFourArgCall(cmd, arg1, arg2, arg3):
	raise ValueError("Wat?")


def customHandler(dummy_signum, dummy_stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt


def parseCommandLine():
	signal.signal(signal.SIGINT, customHandler)
	if len(sys.argv) == 2:
		cmd = sys.argv[1].lower()
		parseOneArgCall(cmd)

	elif len(sys.argv) == 3:
		cmd = sys.argv[1].lower()
		val = sys.argv[2]
		parseTwoArgCall(cmd, val)

	elif len(sys.argv) == 4:

		cmd = sys.argv[1].lower()
		arg1 = sys.argv[2]
		arg2 = sys.argv[3]
		parseThreeArgCall(cmd, arg1, arg2)

	elif len(sys.argv) == 5:

		cmd = sys.argv[1].lower()
		arg1 = sys.argv[2]
		arg2 = sys.argv[3]
		arg3 = sys.argv[4]
		parseFourArgCall(cmd, arg1, arg2, arg3)

	else:
		printHelp()

if __name__ == "__main__":
	print("Command line parse")
	parseCommandLine()


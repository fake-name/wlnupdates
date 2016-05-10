

print("Utilities Startup")


import logSetup
logSetup.initLogging()

import signal
import sys
import os.path

from app import app
from app import api_handlers_admin
import util.db_organize

def printHelp():

	print("################################### ")
	print("##   System maintenance script   ## ")
	print("################################### ")
	print("")
	print("*********************************************************")
	print("Organizing Tools")
	print("*********************************************************")
	print("	lv-merge")
	print("		Use levenshtein string distance metrics to try to heuristically automatically")
	print("		merge series with multiple instances.")
	print()
	return


one_arg_map = {

}


def parseOneArgCall(cmd):


	mainArg = sys.argv[1]

	print ("Passed arg", mainArg)


	with app.app_context():
		arg = mainArg.lower()


		if arg == "flatten-series-by-url":
			print(api_handlers_admin.flatten_series_by_url(None, admin_override=True))
		elif arg == "delete-duplicate-releases":
			print(api_handlers_admin.delete_duplicate_releases(None, admin_override=True))
		elif arg == "fix-escaped-quotes":
			print(api_handlers_admin.fix_escaped_quotes(None, admin_override=True))
		elif arg == "clean-tags":
			print(api_handlers_admin.clean_tags(None, admin_override=True))
		elif arg == "lv-merge":
			util.db_organize.levenshein_merger()
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


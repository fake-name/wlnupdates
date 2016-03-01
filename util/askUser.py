
import sys

def query_response(question):
	valid = {"f":"forward",
			 "r":"reverse",
			 "l":"levenshtein",
			 "n":False}

	prompt = " [f/r/l/N] "

	while True:
		sys.stdout.write(question + prompt)
		choice = input().lower()
		if choice == '':
			return valid["n"]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Invalid choice\n")

def query_response_bool(question):
	valid = {"y":True,
			 "n":False}

	prompt = " [y/N] "

	while True:
		sys.stdout.write(question + prompt)
		choice = input().lower()
		if choice == '':
			return valid["n"]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Invalid choice\n")
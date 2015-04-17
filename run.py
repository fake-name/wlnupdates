#!flask/bin/python
def go():
	from app import app
	import sys
	if "debug" in sys.argv:
		print("Running in debug mode.")
		app.run(debug=True, host='0.0.0.0')
	else:
		print("Running in normal mode.")
		app.run()

if __name__ == "__main__":
	go()

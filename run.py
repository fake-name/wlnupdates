#!flask/bin/python
def go():
	from app import app
	import sys
	if "debug" in sys.argv:
		app.run(debug=True, host='0.0.0.0')
	else:
		app.run()

if __name__ == "__main__":
	go()

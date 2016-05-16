#!flask/bin/python
import pprint
dosort = [
	(1,2,2),
	(1,2,4),
	(1,None,4),
	(1,2,3),
	(2,2,0),
	(2,None,0),
	(1,2,0),
	(1,1,0),
]

def go():
	pprint.pprint(dosort)
	dosort.sort()
	pprint.pprint(dosort)

if __name__ == "__main__":
	go()

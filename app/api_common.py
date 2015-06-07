


def getResponse(message, error=False, shouldReload=True):
	ret = {
		'error'   : error,
		'message' : message,
		'reload'  : shouldReload,
	}
	return ret

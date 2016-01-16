


def getResponse(message, error=False, shouldReload=True):
	ret = {
		'error'   : error,
		'message' : message,
		'reload'  : shouldReload,
	}
	return ret

def getDataResponse(data, message=None, error=False):
	ret = {
		'error'   : error,
		'message' : message,
		'data'    : data,
	}
	return ret

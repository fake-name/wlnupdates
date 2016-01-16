
from app import app
from app.historyController import renderHistory

@app.route('/history/<topic>/<int:srcId>')
def history_route(topic, srcId):
	return renderHistory(topic, srcId)

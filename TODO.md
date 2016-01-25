Todo:
 - Add wiki for tags, etc...
 - Fold multiple releases for the same item in sequence.

deal with single-character author issues (whoops, something wasn't converted to a list).

Done:
## - show how many people watching each ite,
## - special-case annoying ALLCAPS titles, lower case them.
## - unescaped https://www.wlnupdates.com/series-id/32392/
## - Narrow viewport should shrink covers
## - add links to the legal for all the inline deps - jquery, rabbitmq, etc...
## - Removing items from lists doesn't.
## - Fix all the escaped things: (Mostly "\'")

Notes:
I would like to suggest that in the list of series, you have ways of sorting the series by popularity, by rating, by editor's choice (your personal favorites), by state of completion, stuff like that.

I would also suggest that in the list of all the novels, next to the series, you have their state of completion and the last chapter translated. So it would read like "Akikan - Incomplete - Chapter 243/9000" or whatever.


http://topwebfiction.com/
http://webfictionguide.com/

## https://www.wattpad.com/home
## http://storiesonline.net/
## https://www.fictionpress.com
## http://www.booksie.com/
## https://www.fanfiction.net/



404. Wat?
404. Wat?
404. Wat?
404. Wat?
Json request: {'mode': 'set-watch', 'watch': True, 'item-id': '34919', 'list': 'Inbox'}
[setSeriesWatchJson] data ->  {'mode': 'set-watch', 'watch': True, 'item-id': '34919', 'list': 'Inbox'}
Trying to validate
Json request: {'mode': 'merge-id', 'merge_id': '409', 'item-id': '34649'}
Internal Error!
'Response' object is not iterable
Traceback (most recent call last):
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/flask/app.py", line 1817, in wsgi_app
    response = self.full_dispatch_request()
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/flask/app.py", line 1477, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/flask/app.py", line 1381, in handle_user_exception
    reraise(exc_type, exc_value, tb)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/flask/_compat.py", line 33, in reraise
    raise value
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/flask/app.py", line 1475, in full_dispatch_request
    rv = self.dispatch_request()
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/flask/app.py", line 1461, in dispatch_request
    return self.view_functions[rule.endpoint](**req.view_args)
  File "/media/Storage/wlnupdates/app/sub_views/item_views.py", line 180, in renderSeriesId
    series, releases, watch, watchlists, progress, latest, latest_dict, most_recent, latest_str, rating, total_watches = load_series_data(sid)
TypeError: 'Response' object is not iterable


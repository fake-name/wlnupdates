## Removing items from lists doesn't.
Narrow viewport should shrink covers

I would like to suggest that in the list of series, you have ways of sorting the series by popularity, by rating, by editor's choice (your personal favorites), by state of completion, stuff like that.

I would also suggest that in the list of all the novels, next to the series, you have their state of completion and the last chapter translated. So it would read like "Akikan - Incomplete - Chapter 243/9000" or whatever.



Error:


127.0.0.1 - - [19/Jun/2015 21:14:23] "GET /static/css/bootstrap.css HTTP/1.0" 200 -
127.0.0.1 - - [19/Jun/2015 21:14:23] "GET /static/css/custom.css HTTP/1.0" 200 -
127.0.0.1 - - [19/Jun/2015 21:14:23] "GET /static/js/bootstrap.min.js HTTP/1.0" 200 -
127.0.0.1 - - [19/Jun/2015 21:14:23] "GET /static/js/jquery-latest.min.js HTTP/1.0" 200 -
127.0.0.1 - - [19/Jun/2015 21:14:23] "GET /static/fonts/glyphicons-halflings-regular.woff2 HTTP/1.0" 304 -
127.0.0.1 - - [19/Jun/2015 21:14:23] "GET /favicon.ico HTTP/1.0" 200 -
Connection dropped! Attempting to reconnect!
Failed pre-emptive closing before reconnection. May not be a problem?
Traceback (most recent call last):
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 203, in _poll
    self.active += self._processReceiving()
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 246, in _processReceiving
    item = self.channel.basic_get(queue=in_queue)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/channel.py", line 1951, in basic_get
    self._send_method((60, 70), args)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/abstract_channel.py", line 56, in _send_method
    self.channel_id, method_sig, args, content,
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/method_framing.py", line 221, in write_method
    write_frame(1, channel, payload)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 182, in write_frame
    frame_type, channel, size, payload, 0xce,
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 254, in _write
    n = write(s)
  File "/usr/lib/python3.4/ssl.py", line 638, in write
    return self._sslobj.write(data)
BrokenPipeError: [Errno 32] Broken pipe

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 218, in _poll
    self.connection.close()
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/connection.py", line 461, in close
    self._send_method((10, 50), args)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/abstract_channel.py", line 56, in _send_method
    self.channel_id, method_sig, args, content,
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/method_framing.py", line 221, in write_method
    write_frame(1, channel, payload)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 182, in write_frame
    frame_type, channel, size, payload, 0xce,
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 254, in _write
    n = write(s)
  File "/usr/lib/python3.4/ssl.py", line 638, in write
    return self._sslobj.write(data)
ssl.SSLError: [SSL: BAD_WRITE_RETRY] bad write retry (_ssl.c:1636)

Exception in thread Thread-2:
Traceback (most recent call last):
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 203, in _poll
    self.active += self._processReceiving()
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 246, in _processReceiving
    item = self.channel.basic_get(queue=in_queue)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/channel.py", line 1951, in basic_get
    self._send_method((60, 70), args)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/abstract_channel.py", line 56, in _send_method
    self.channel_id, method_sig, args, content,
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/method_framing.py", line 221, in write_method
    write_frame(1, channel, payload)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 182, in write_frame
    frame_type, channel, size, payload, 0xce,
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 254, in _write
    n = write(s)
  File "/usr/lib/python3.4/ssl.py", line 638, in write
    return self._sslobj.write(data)
BrokenPipeError: [Errno 32] Broken pipe

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.4/threading.py", line 920, in _bootstrap_inner
    self.run()
  File "/usr/lib/python3.4/threading.py", line 868, in run
    self._target(*self._args, **self._kwargs)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 167, in _poll_proxy
    self._poll()
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 224, in _poll
    self._connect()
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/AmqpConnector/__init__.py", line 129, in _connect
    ssl          =self.sslopts)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/connection.py", line 165, in __init__
    self.transport = self.Transport(host, connect_timeout, ssl)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/connection.py", line 186, in Transport
    return create_transport(host, connect_timeout, ssl)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 297, in create_transport
    return SSLTransport(host, connect_timeout, ssl)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 199, in __init__
    super(SSLTransport, self).__init__(host, connect_timeout)
  File "/media/Storage/wlnupdates/flask/lib/python3.4/site-packages/amqp/transport.py", line 95, in __init__
    raise socket.error(last_err)
OSError: [Errno 111] Connection refused

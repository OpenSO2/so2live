import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import base64
import matplotlib.pyplot as plt
import numpy as np
import socket
import struct
import time
import sys
import tempfile
from scipy import misc

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[1], int(sys.argv[2])))

def r(c):
	img = tempfile.TemporaryFile()

	l = struct.pack("I", 3)
	cmd = struct.pack("ccc", c[0], c[1], c[2])

	print "send length"
	s.send(l)

	print "send cmd"
	s.send(cmd)

	buf = ''
	while len(buf) < 4:
		print "len is smaller than 4,", len(buf)
		buf += s.recv(4 - len(buf))
	size = struct.unpack('i', buf)[0]

	print "receiving %s bytes" % size

	while True:
		data = s.recv(1024)
		if not data:
			print "no data, break"
			break

		size -= len(data)

		img.write(data)

		if size == 0:
			break

		print "recv'd size", len(data)

	img.seek(0)
	return img

class IndexHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self):
		self.render('./index.html')

class WebSocketHandler(tornado.websocket.WebSocketHandler):

	def initialize(self):
		pass

	def open(self):
		print 'new connection'

	def on_message(self, message):
		if message == "top":
			t = r("top")
		elif message == "bot":
			t = r("bot")
		elif message == "cam":
			t = r("cam")
		else:
			return True
		src = base64.b64encode(t.read())
		self.write_message({"type": message, "data": src})
		print message

	def on_close(self):
		print 'connection closed'

if __name__ == '__main__':

	application = tornado.web.Application([
		(r'/', IndexHandler),
		(r'/ws', WebSocketHandler),
	])

	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8888)
	tornado.ioloop.IOLoop.instance().start()

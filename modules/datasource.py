"""Datasource for liveview.

This class abstracts the connection/interface to the so2control software so
that implementers do not need to worry about the details.
ATM, only periodically requesting new data (polling) is supported, in the
future (hopefully) pushing will also be implemented.
"""
from __future__ import print_function
import socket
import struct
import time
import re
import threading
import numpy as np
import cv2


class DataSource(object):
	"""Handles the connection and interfacing with the so2control software."""

	_queue = {
		"top": [],
		"bot": [],
		"cam": [],
		"spc": [],
		"cmp": [],
	}

	_socket = None
	_timer = None

	def connect(self, addr, port):
		"""Establish a connection to the so2control software.

		This might fail eg. when the port is blocked by a firewall.
		"""
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Wait for socket to appear and retry every second
		connected = False
		while not connected:
			try:
				self._socket.connect(addr, port)
				connected = True
				print("connected")
			except socket.error:
				print("not yet connected")
				time.sleep(1)

	def _sendcommand(self, command):
		length = struct.pack("I", 3)
		cmd = struct.pack("ccc", command[0].encode('ascii'),
							command[1].encode('ascii'), command[2].encode('ascii'))

		self._socket.send(length)
		self._socket.send(cmd)

	def _receive(self):
		buf = b''
		while len(buf) < 4:
			buf += self._socket.recv(4 - len(buf))
		size = struct.unpack('i', buf)[0]

		if size == 0:
			return [], []

		buf = b''
		while len(buf) < size:
			buf += self._socket.recv(size - len(buf))

		return buf

	@staticmethod
	def _handleimg(buf):
		arr = np.asarray(bytearray(buf))
		data = {}

		for mesg in re.finditer(b'tEXt', buf):
			length = int(arr[mesg.start() - 1])
			text = buf[mesg.end():mesg.end() + length]
			if b'Creation Time' in text:
				data["Creation Time"] = text.replace(b'Creation Time\x00', b'')
			else:
				key, content = text.split(b': ')
				key = re.sub(b'^Comment\x00', b'', key)
				data[key] = content

		image_2d = cv2.imdecode(arr, -1)  # 'load it as it is'
		shape = np.shape(image_2d)
		if len(shape) > 2 and shape[2] == 3:
			image_2d = cv2.cvtColor(image_2d, cv2.COLOR_BGR2RGB)

		return image_2d, data

	@staticmethod
	def _handlespc(buf):
		# fixme: hardcoded spectrum length
		rang = range(0, 2048 * 8, 8)
		return [struct.unpack('<d', buf[i:i + 8])[0] for i in rang], {}

	def _getdata(self, command):
		self._sendcommand(command)
		buf = self._receive()

		if command == "spc":
			image_2d, data = self._handlespc(buf)
		else:
			image_2d, data = self._handleimg(buf)

		data["name"] = command

		return image_2d, data

	def run_perio(self):
		"""Start to periodically fetch updates from the camera."""
		for typ in self._queue:
			if self._queue[typ]:
				self._run(typ)
		self._timer = threading.Timer(1, self.run_perio)
		self._timer.start()

	def stop_perio(self):
		"""Stop trying to fetch updates."""
		self._timer.cancel()

	def listen(self, what, callback):
		"""Subscribe to a camera event. Callback runs when new data is available."""
		self._queue[what].append(callback)

	def _run(self, what):
		img, data = self._getdata(what)
		if img:
			for fct in self._queue[what]:
				fct(img, data)

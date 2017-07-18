import matplotlib.pyplot as plt
import numpy as np
import socket
import struct
import sys
import cv2

if (len(sys.argv) != 3):
	print "usage: ", sys.argv[0], "tcp-socket-address", "tcp-socket-port"
	print "eg:    ", sys.argv[0], "localhost", "27000"
	exit(-1)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Wait for socket to appear and retry every second
connected = False
while not connected:
	try:
		s.connect((sys.argv[1], int(sys.argv[2])))
		connected = True
	except Exception as e:
		print "not yet connected"
		time.sleep(1)

def r(c):
	l = struct.pack("I", 3)
	cmd = struct.pack("ccc", c[0], c[1], c[2])

	s.send(l)
	s.send(cmd)

	buf = ''
	while len(buf) < 4:
		buf += s.recv(4 - len(buf))
	size = struct.unpack('i', buf)[0]

	buf = ''
	while len(buf) < size:
		buf += s.recv(size - len(buf))

	arr = np.asarray(bytearray(buf), dtype=np.uint8)
	image_2d = cv2.imdecode(arr,-1) # 'load it as it is'
	shape = np.shape(image_2d)
	if len(shape) > 2 and shape[2] == 3:
		image_2d = np.reshape(image_2d, (shape[1], shape[0], shape[2]))
		image_2d = cv2.cvtColor(image_2d, cv2.COLOR_BGR2RGB)

	return image_2d


plt.ion()
fig = plt.figure()

bot = fig.add_subplot(131)
top = fig.add_subplot(132)
cam = fig.add_subplot(133)
plt.show()

botimg = False
topimg = False
camimg = False

while 1:
	img = r("bot")
	if botimg:
		print "!! update botimg"
		botimg.set_data(img)
	else:
		print "!! imshow botimg"
		botimg = bot.imshow(img, cmap='gray')


	img = r("top")
	if topimg:
		print "!! update topimg"
		topimg.set_data(img)
	else:
		print "!! imshow topimg"
		topimg = top.imshow(img, cmap='gray')


	img = r("cam")
	if camimg:
		print "!! update camimg"
		camimg.set_data(img)
	else:
		print "!! imshow camimg"
		camimg = cam.imshow(img)

	plt.draw()
	plt.pause(.001)



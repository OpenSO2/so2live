import matplotlib.pyplot as plt
import numpy as np
import socket
import struct
import time

from PIL import Image

import io
import sys
import tempfile
from scipy import misc
import errno
from matplotlib.widgets import Slider, Button, RadioButtons
import matplotlib.image as mpimg

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

	print "send length"
	print s
	s.send(l)

	#~ print "send cmd"
	s.send(cmd)

	buf = ''
	while len(buf) < 4:
		buf += s.recv(4 - len(buf))
	size = struct.unpack('i', buf)[0]
	print "receiving %s bytes" % size

	img_rcv = np.empty(size, dtype = np.int16)
	p = s.recv_into(img_rcv, int(size), socket.MSG_WAITALL)

	img_rcv.tofile("temp.png")
	img_rcv = mpimg.imread('temp.png')

	return img_rcv




plt.ion()
fig = plt.figure()
#~ ax = fig.add_subplot(111)

#~ fig, ax = plt.subplots(111)
#~ plt.subplots_adjust(left=0.25, bottom=0.25)
#~ t = np.arange(0.0, 1.0, 0.001)
a0 = 5
f0 = 3
#~ s = a0*np.sin(2*np.pi*f0*t)
#~ l, = plt.plot(t, s, lw=2, color='red')
#~ plt.axis([0, 1, -10, 10])

axfreq = plt.axes([0.15, 0.5, 0.20, 0.03])
axamp = plt.axes([0.40, 0.5, 0.20, 0.03])

sfreq = Slider(axfreq, 'Freq', 0.1, 30.0, valinit=f0)
samp = Slider(axamp, 'Amp', 0.1, 10.0, valinit=a0)

def update(val):
    print "update"
    #~ amp = samp.val
    #~ freq = sfreq.val
    #~ l.set_ydata(amp*np.sin(2*np.pi*freq*t))
    #~ fig.canvas.draw_idle()
sfreq.on_changed(update)
samp.on_changed(update)



bot = fig.add_subplot(231)
top = fig.add_subplot(232)
cam = fig.add_subplot(233)
plt.show()


while 1:
	img = r("bot")
	bot.imshow(img, cmap='gray')

	img = r("top")
	top.imshow(img, cmap='gray')

	img = r("cam")
	cam.imshow(img)

	plt.pause(1)





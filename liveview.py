"""A simple live view sample application to demonstrate the datasource module.

It has two views: an overview and a overlay view. The latter is
useful for camera alignment and focusing

  View 1:
  |-------| |------------------|  |-------|
  |310nm  | | compound         |  |webcam |
  |       | |                  |  |       |
  |-------| |                  |  |-------|
            |                  |
  |-------| |                  |  |-------|
  |330nm  | |                  |  |spectro|
  |       | |                  |  |       |
  |-------| |------------------|  |-------|

                  [ Overlay toggle button ]


  View 2:
  |---------------------------------------|
  | overlay of 310 over 330nm image       |
  |                                       |
  |                                       |
  |                                       |
  |                                       |
  |                                       |
  |                                       |
  |                                       |
  |                                       |
  |---------------------------------------|

  |--Overlay slider---------*-------------| 70%

                  [ Overlay toggle button ]

"""
from __future__ import print_function
from __future__ import division
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button
from modules.datasource import DataSource

if len(sys.argv) != 2:
	print("usage: ", sys.argv[0], "tcp-socket-address:tcp-socket-port")
	print("eg:    ", sys.argv[0], "localhost:7009")
	exit(-1)


class Liveview(object):
	"""Simple live view gui."""

	host, port = sys.argv[1].split(":")
	host = host or "localhost"
	port = port or "7009"

	datasource = DataSource()

	gsp = gridspec.GridSpec(2, 4, left=0.01, bottom=0.01, right=.99, top=0.99,
						wspace=0.04, hspace=0.04)
	gsp2 = gridspec.GridSpec(1, 1, left=0.01, bottom=0.01, right=.99, top=0.99)

	axs = {}
	imgs = {}

	bot = top = None
	visible = False

	def __init__(self):
		"""Start the gui."""
		self.fig = plt.figure(figsize=(11, 4))
		self.datasource.connect(self.host, int(self.port))
		self.datasource.run_perio()

		self.axs["bot"] = self.fig.add_subplot(self.gsp[0, 0])
		self.axs["top"] = self.fig.add_subplot(self.gsp[1, 0])
		self.axs["abs"] = self.fig.add_subplot(self.gsp[0:2, 1:3])
		self.axs["cam"] = self.fig.add_subplot(self.gsp[0, -1])
		self.axs["spc"] = self.fig.add_subplot(self.gsp[1, -1])
		self.axs["ovl"] = self.fig.add_subplot(self.gsp2[0, 0])

		self.imgs["bot"] = self.axs["bot"].imshow([[0]], cmap='gray')
		self.imgs["top"] = self.axs["top"].imshow([[0]], cmap='gray')
		self.imgs["abs"] = self.axs["abs"].imshow([[0]], cmap='gray')
		self.imgs["cam"] = self.axs["cam"].imshow([[0]])
		self.imgs["spc"], = self.axs["spc"].plot([0], [0])
		self.imgs["ovlbot"] = self.axs["ovl"].imshow([[0]], cmap='gray')
		self.imgs["ovltop"] = self.axs["ovl"].imshow([[0]], cmap='gray')

		for item in "bot top abs cam ovl spc".split(" "):
			self.axs[item].set_yticklabels([])
			self.axs[item].set_xticklabels([])
			self.axs[item].set_yticks([])
			self.axs[item].set_xticks([])

		# add slide to choose the transparency of the overlayed image
		self.axtrans = plt.axes([0.25, 0.15, 0.65, 0.03])
		strans = Slider(self.axtrans, 'Transparency', 0., 1., valinit=.5)
		strans.on_changed(self.imgs["ovltop"].set_alpha)
		self.imgs["ovltop"].set_alpha(.5)

		self.update_absimg = self.makeupdatefunc("abs")

		self.toggle_visibility(None)

		btnax = plt.axes([0.8, 0.025, 0.1, 0.04])
		button = Button(btnax, 'Overlay mode')
		button.on_clicked(self.toggle_visibility)

		self.datasource.listen("bot", self.makeupdatefunc("bot"))
		self.datasource.listen("top", self.makeupdatefunc("top"))
		self.datasource.listen("bot", self.update_abs)
		self.datasource.listen("top", self.update_abs)
		self.datasource.listen("top", self.makeupdatefunc("ovltop"))
		self.datasource.listen("bot", self.makeupdatefunc("ovlbot"))
		self.datasource.listen("cam", self.makeupdatefunc("cam"))
		self.datasource.listen("spc", self.makeupdatefunc_spc())

		plt.show()
		self.datasource.stop_perio()

	def makeupdatefunc(self, val):
		"""Create the update functions."""
		def update(data, _):
			"""Update the source image."""
			self.imgs[val].set_data(data)
			self.imgs[val].set_clim(data.min(), data.max())
			self.axs[val[:3]].set_aspect(data.shape[0] / data.shape[1])
			plt.draw()
		return update

	def makeupdatefunc_spc(self):
		"""Create the update functions."""
		def update_spc(data, _):
			"""Update spectrum."""
			self.imgs["spc"].set_data(range(0, len(data)), data)
			self.axs["spc"].relim()
			self.axs["spc"].autoscale_view()
			plt.draw()
		return update_spc

	@staticmethod
	def calc_abs(i310, i330):
		"""Very roughly calculate absorbance."""
		return -np.log10(i310 / i330)

	def update_abs(self, data, metadata):
		"""Update absorbance image."""
		if metadata["name"] == "top":
			self.top = data
		if metadata["name"] == "bot":
			self.bot = data

		if self.bot is None or self.top is None:
			return

		img = self.calc_abs(self.top, self.bot)
		self.update_absimg(img, None)
		plt.draw()

	def toggle_visibility(self, _):
		"""Toggle between the two views."""
		self.visible = not self.visible
		self.axs["cam"].set_visible(self.visible)
		self.axs["top"].set_visible(self.visible)
		self.axs["bot"].set_visible(self.visible)
		self.axs["spc"].set_visible(self.visible)
		self.axs["ovl"].set_visible(not self.visible)
		self.axtrans.set_visible(not self.visible)
		plt.draw()


Liveview()

#!/usr/bin/env python

import sys, os

class L298Driver:
	pwmPins = []
	dirPins= []
	maxDC = 100
	minDC = 20

	gpioQueue = None

	def __init__(self, gpioQueue):
		self.gpioQueue = gpioQueue
		sys.path.append(os.path.abspath('..'))
		import util
		# TODO replace this with a read from a file
		if util.microcontroller == 'Edision':
			self.pwmPins = [5, 6]
			self.dirPins = [[7, 8], [10, 9]] 
		elif util.microcontroller == 'RPi':
			self.pwmPins = [38, 37]
			self.dirPins = [[31,32], [33,35]]
		self.gpioQueue.put(['setup', self.pwmPins, ['PWM', 'PWM']])
		self.gpioQueue.put(['setupPWM', self.pwmPins, [60, 60]])
		self.gpioQueue.put(['setup', self.dirPins[0], ['OUTPUT', 'OUTPUT']])
		self.gpioQueue.put(['setup', self.dirPins[1], ['OUTPUT', 'OUTPUT']])

	def setDirection(self, direction):
		for i in range(0, 2):
			if direction[i]:
				self.gpioQueue.put(['write', self.dirPins[i][0], 1])
				self.gpioQueue.put(['write', self.dirPins[i][1], 0])
			else:
				self.gpioQueue.put(['write', self.dirPins[i][0], 0])
				self.gpioQueue.put(['write', self.dirPins[i][1], 1])

	# set PWM duty cycle
	# powers should be an array with 2 indexes [mLeftPower, mRightPower]
	# direction should be an array with 2 indexes [mLeftDir, mRightDir]
	def setDC(self, powers, direction):
		self.setDirection(direction)
		for i in range(0, len(powers)):
			self.gpioQueue.put(['setDC', self.pwmPins[i], powers[i]])

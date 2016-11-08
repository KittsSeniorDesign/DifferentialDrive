#!/usr/bin/env python

import sys, os
sys.path.append(os.path.abspath('..'))
import util

class L298Driver:
	pwmPins = []
	dirPins= []
	maxDC = 100
	minDC = 20


	def __init__(self):
		sys.path.append(os.path.abspath('..'))
		import util
		# TODO replace this with a read from a file
		if util.microcontroller == 'Edison':
			self.pwmPins = [5, 9]
			self.dirPins = [[7, 8], [10, 6]] 
		elif util.microcontroller == 'RPi':
			self.pwmPins = [38, 37]
			self.dirPins = [[31,32], [33,35]]
		util.gpioQueue.put(['setup', self.pwmPins, ['PWM', 'PWM']])
		util.gpioQueue.put(['setupPWM', self.pwmPins, [60, 60]])
		util.gpioQueue.put(['setup', self.dirPins[0], ['OUTPUT', 'OUTPUT']])
		util.gpioQueue.put(['setup', self.dirPins[1], ['OUTPUT', 'OUTPUT']])

	def setDirection(self, direction):
		for i in range(0, 2):
			if direction[i]:
				util.gpioQueue.put(['write', self.dirPins[i][0], 1])
				util.gpioQueue.put(['write', self.dirPins[i][1], 0])
			else:
				util.gpioQueue.put(['write', self.dirPins[i][0], 0])
				util.gpioQueue.put(['write', self.dirPins[i][1], 1])

	# set PWM duty cycle
	# powers should be an array with 2 indexes [mLeftPower, mRightPower]
	# direction should be an array with 2 indexes [mLeftDir, mRightDir]
	def setDC(self, powers, direction):
		self.setDirection(direction)
		for i in range(0, len(powers)):
			util.gpioQueue.put(['setDC', self.pwmPins[i], powers[i]])

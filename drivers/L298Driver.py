#!/usr/bin/env python

class L298Driver:
	pwmPins = []
	dirPins= []
	maxDC = 100
	minDC = 20

	gpioQueue = None

	def __init__(self, gpioQueue):
		# TODO replace this with a read from a file
		self.gpioQueue = gpioQueue
		if util.microController == 'Edision':
			pwmPins = [5, 6]
			dirPins = [[7, 8], [10, 9]] 
		elif util.microcontroller == 'RPi'
			pwmPins = [38, 37]
			dirPins = [[31,32], [33,35]]
		self.gpioQueue.put(['setupPWM', pwmPins, [60, 60]])
		self.gpioQueue.put(['setup', dirPins[0], ['OUTPUT', 'OUTPUT']])
		self.gpioQueue.put(['setup', dirPins[1], ['OUTPUT', 'OUTPUT']])

	def setDirection(self, direction):
		for i in range(0, 2):
			if direction[i]:
				self.gpioQueue.put(['write', self.dirPin[i][0], 1])
				self.gpioQueue.put(['write', self.dirPin[i][1], 0])
			else:
				self.gpioQueue.put(['write', self.dirPin[i][0], 0])
				self.gpioQueue.put(['write', self.dirPin[i][1], 1])

	# set PWM duty cycle
	# powers should be an array with 2 indexes [mLeftPower, mRightPower]
	# direction should be an array with 2 indexes [mLeftDir, mRightDir]
	def setDC(self, powers, direction)
		self.setDirection(direction)
		for i in range(0, len(powers)):
			self.gpioQueue.put(['setDC', pwmPins[i], powers[i]])
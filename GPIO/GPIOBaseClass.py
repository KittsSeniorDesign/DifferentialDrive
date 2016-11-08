#!/usr/bin/env python

from multiprocessing import Process
from multiprocessing import Queue
import time, os, sys

sys.path.append(os.path.abspath('..'))
import util

class GPIOBaseClass(Process):
	
	OUTPUT = "Override in inherited class"
	INPUT = "Override in inherited class"
	PWM = "Override in inherited class"
	ANALOG_INPUT = "Override in inherited class"

	encDict = {}

	# childs init should call the super constructor 
	# and things like 
	#	GPIO.setmode() if raspberry pi 
	#	or GPIO(debug=False) if edison
	def __init__(self, encoderPins):
		super(GPIOBaseClass, self).__init__()
		for p in encoderPins:
			self.setupWaitForEdgeISR(self.edgeDetected, p)

	# pins should be a tuple of which pins to setup
	# modes should be the corresponding mode for each pin in pins
	# should do something like
	# if len(pins) > 1:
	#		for i in range(0, len(pins)):
	#			GPIO.setupPin(pins[i], modes[i]) # or respective code for platform
	# elif len(pins) == 1:
	# 		GPIO.setupPin(pins, modes)	
	def setup(self, pins, modes):
		raise NotImplementedError("Override setup in class that inherits GPIOBaseClass")

	# pins should be a tuple of which pins to use for pwm
	# frequencies should be the corresponding PWM wave frequencies in herts for each pin
	# should be very similar to setupPins
	def setupPWM(self, pins, frequencies):
		raise NotImplementedError("Override setupPWM in class that inherits GPIOBaseClass")

	# args should be tuples, lists or a single int
	# changes the frequencies of the pwm signals on pins
	def changeFrequency(self, pins, frequencies):
		raise NotImplementedError("Override changeFrequency in class that inherits GPIOBaseClass")

	# args should be tuples, lists or a single int
	# sets the duty cycle of the pwm signal on the pwm pins based on powers
	# value should be between 0-100, but some implementations may have an actual resolution of 255
	def setDC(self, pins, values):
		raise NotImplementedError("Override setDC in class that inherits GPIOBaseClass")

	# args should be tuples, lists or a single int
	# writes the values in levels to the corresponding pin in pins
	def write(self, pins, levels):
		raise NotImplementedError("Override writeToPin in class that inherits GPIOBaseClass")

	# pin is not a list, or tuple! It is a single pin
	# _read should return the digital value of the pin, do a digitalRead()
	def _read(self, pin):
		raise NotImplementedError("Override _read in class that inherits GPIOBaseClass")

	# pin is not a list, or tuple! It is a single pin
	# _analogRead should return the analogReading of the pin, doesn't make sense with RPi, need adc
	def _analogRead(self, pin):
		raise NotImplementedError("Override _analogRead in class that inherits GPIOBaseClass")

	# should still override this function to cleanup gpio and pwm stuff
	# but also make sure to call this function from the super class
	def exitGracefully(self):
		# this is done to break out of the while loop in run so process terminates
		util.gpioQueue = None
		#for p in self.waitingProcs:
		#	p.join()

	def consumeQueue(self):
		while not util.gpioQueue.empty():
			a = util.gpioQueue.get_nowait()
			if a:
				if a[0] == 'setup':
					# a[1] is pins
					# a[2] is modes
					self.setup(a[1], a[2])
				elif a[0] == 'setupPWM':
					# a[1] is pins
					# a[2] is frequencies
					self.setupPWM(a[1], a[2])
				elif a[0] == 'changeFrequency':
					# a[1] is pins
					# a[2] is frequencies
					self.changeFrequency(a[1], a[2])
				elif a[0] == 'setDC':
					# a[1] is pins
					# a[2] is values
					self.setDC(a[1], a[2])
				elif a[0] == 'write':
					# a[1] is pins
					# a[2] is levels
					self.write(a[1], a[2])
				elif a[0] == 'exitGracefully':
					self.exitGracefully()
				elif a[0] == 'waitForEdge':
					# a[1] = callback function for the isr
					# a[2] = pin to wait for an edge
					self.setupWaitForEdgeISR(a[1], a[2])
				elif a[0] == 'analogRead':
					# a[1] = uniqueProcessIdentifier
					# a[2] = pin to read
					raise NotImplementedError("analogRead is unsupported")
				elif a[0] == 'resetEncoders':
					for key in encDict:
						encDict[key].resetPeriod()

	# it is assumed that the pin is already setup
	def setupWaitForEdgeISR(self, callback, pin):
		raise NotImplementedError("Override _setupWaitForEdgeISR in class that inherits GPIOBaseClass")

	def edgeDetected(self):
		raise NotImplementedError("Override edgeDetected in class that inherits GPIOBaseClass.")

	def run(self):
		try:
			a = None
			while util.gpioQueue:
				self.consumeQueue()
		except KeyboardInterrupt as msg:
			print "KeyboardInterrupt detected. GPIOProcess is terminating"
		finally:
			self.exitGracefully()




	count = 0
	pSize = 10
	periods = [-1.0]*pSize
	periodIndex = 0
	timeout = .1
	lastEdge = 0

	def edgeDetected(self, pin):
		self.count += 1
		ctime = time.time()
		elapsedTime = ctime-self.lastEdge
		if elapsedTime <= self.timeout:
			self.periods[self.periodIndex] = elapsedTime
		# increment self.periodIndex and keep it within range of self.pSize = len(self.periods)
			self.periodIndex = (self.periodIndex+1)%self.pSize;
		self.lastEdge = ctime
		util.encQueue.put([self.count])

	def resetPeriod(self):
		self.periods = [-1]*self.pSize
		self.periodIndex = 0

	# returns seconds/blip
	def getAveragePeriodBetweenBlips(self):
		ave = 0.0
		i = 0
		for i in range(0, self.pSize):
			if self.periods[i] == -1: # invalid period, therefore return what is got
				break
			else:
				ave += self.periods[i]
		# return average of valid periods, i+1 because i will never equal self.pSize
		if i < 10:
			return -1
		else:
			return ave/(i+1)

	# if level = None a stall occured
	def waitForEdgeResponse(self, level, elapsedTime):
		if elapsedTime >= self.timeout: #Stall occured
			#TODO handle stall
			print "OH NO! A STALL"
			self.count = 0
			self.resetPeriod()
		else:
			self.count += 1
			self.periods[self.periodIndex] = elapsedTime
	# increment self.periodIndex and keep it within range of self.pSize = len(self.periods)
			self.periodIndex = (self.periodIndex+1)%self.pSize;
		util.encQueue.put([self.pin ,self.count, self.getAveragePeriodBetweenBlips()])
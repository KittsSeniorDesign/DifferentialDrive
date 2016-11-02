#!/usr/bin/env python

from multiprocessing import Process
from multiprocessing import Queue
import time

class PinWaiter(Process):
	gpio = None 
	pin = None
	timeout = None
	pipe = None

	def __init__(self, gpiobaseclass, pin, timeout, pipe):
		super(PinWaiter, self).__init()
		self.gpio = gpiobaseclass
		self.pin = pin
		self.timeout = timeout
		self.pipe = pipe
		self.start()

	def run(self)
		starttime = time.time()
		initLevel = self.gpio._read(self.pin)
		while time.time()-starttime < self.timeout and self.gpio._read(self.pin) == initLevel:
			pass
			# test preformace with and without
			#time.sleep(.001)
		self.pipe.send([self.pin, !initLevel time.time()-starttime])
		self.gpio.waitProcesses.remove(self)

class GPIOBaseClass(Process):
	
	OUTPUT = "Override in inherited class"
	INPUT = "Override in inherited class"
	PWM = "Override in inherited class"
	ANALOG_INPUT = "Override in inherited class"

	# set in __init__
	# used to change pin or pwm values, or to request a input or analog read
	commandQueue = None
	# dictionary of the form {uniqueProcessIdentifier: responsePipe, ...} where responsePipe is a connection object
	responsePipes = None

	waitProcesses = []

	# childs init should call the super constructor 
	# and things like 
	#	GPIO.setmode() if raspberry pi 
	#	or GPIO(debug=False) if edison
	def __init__(self, commandQueue, responsePipes):
		super(GPIOBaseClass, self).__init__()
		self.commandQueue = commandQueue
		self.responsePipes = responsePipes

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
		self.commandQueue = None

	def consumeQueue(self):
		while not self.commandQueue.empty():
			a = self.commandQueue.get_nowait()
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
					self.exitGracefuly()
				elif a[0] == 'waitForEdge':
					# a[1] = uniqueProcessIdentifier
					# a[2] = pin to wait for an edge
					# a[3] = timeout to wait in seconds
					self.waitProcesses.append(PinWaiter(self, a[2], a[3], self.responsePipes[a[1]]))
				elif a[0] == 'analogRead':
					# a[1] = uniqueProcessIdentifier
					# a[2] = pin to read
					self.responsePipes[a[1]].send(self._analogRead(a[2]))

	def run(self):
		try:
			a = None
			while self.commandQueue:
				self.consumeQueue()
		except KeyboardInterrupt as msg:
			print "KeyboardInterrupt detected. GPIOProcess is terminating"
		finally:
			self.exitGracefully()

#!/usr/bin/env python

from GPIOBaseClass import GPIOBaseClass
from wiringx86 import GPIOEdison as GPIO
import sys, os

class EdisonGPIODriver(GPIOBaseClass):
	_gpio = None


	def __init__(self, commandQueue, responsePipes):
		super(EdisonGPIODriver, self).__init__(commandQueue, responsePipes)
		# so we can see util
		sys.path.append(os.path.abspath('..'))
		import util
		self._gpio = GPIO(debug=False)
		OUTPUT = self._gpio.OUTPUT
		INPUT = self._gpio.INPUT
		PWM = self._gpio.PWM
		ANALOG_INPUT = self._gpio.ANALOG_INPUT

	# args should be tuples, list, or a single int
	def setup(self, pins, modes):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				if modes[i] == 'INPUT':
					self._gpio.pinMode(pins[i], self.INPUT)
				elif modes[i] == 'OUTPUT':
					self._gpio.pinMode(pins[i], self.OUTPUT)
				elif modes[i] == 'ANALOG_INPUT':
					self._gpio.pinMode(pins[i], self.ANALOG_INPUT)
				elif modes[i] == 'PWM':
					self._gpio.pinMode(pins[i], self.PWM)
		else:
			if modes == 'INPUT':
				self._gpio.pinMode(pins, self.INPUT)
			elif modes == 'OUTPUT':
				self._gpio.pinMode(pins, self.OUTPUT)
			elif modes == 'ANALOG_INPUT':
				self._gpio.pinMode(pins, self.ANALOG_INPUT)
			elif modes == 'PWM':
				self._gpio.pinMode(pins, self.PWM)

	# args should be tuples, lists, or a single int
	def setupPWM(self, pins, frequencies):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				self._gpio.setPWMPeriod(pins[i], 1.0/frequencies[i])
				self._gpio.analogWrite(pins[i], 0)
		else: # must be an int
			self._gpio.setPWMPeriod(pins, 1.0/frequencies[i])
			self._gpio.analogWrite(pins, 0)

	# args should be tuples, lists, or a single int
	# it is assumed that the entries of pins are already setup as PWM outputs
	def changeFrequency(self, pins, frequencies):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				self._gpio.setPWMPeriod(pins[i], 1.0/frequencies[i])
		else: # must be an int
			self._gpio.setPWMPeriod(pins, 1.0/frequencies)

	# args should be tuples, lists, or a single int
	# it is assumed that the entries of pins are already setup as PWM outputs
	def setDC(self, pins, values):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				if values[i] >= 0 and values[i] <= 100:
					# transform is done because analogWrite has a range from 0-100 for duty cycle values
					self._gpio.analogWrite(pins[i], util.transform(values[i], 0, 100, 0, 255))
				else:
					print "Incorrect duty cycle value was provided"
		else: # mut be an int
			if values >- 0 and values <= 100:
				# transform is done because analogWrite has a range from 0-100 for duty cycle values
				self._gpio.analogWrite(pins, util.transform(values, 0, 100, 0, 255))

	# args should be tuples, lists, or a single int
	# it is assumed that the pins are already setup to be outputs
	def write(self, pins, levels):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				val = self.LOW
				if levels[i]:
					val = self.HIGH
				self._gpio.digitalWrite(pins[i], val)
		else: # must be an int
			val = self.LOW
			if levels:
				val = self.HIGH
			self._gpio.digitalWrite(pins, levels)

	# ait is assumed that the pin was setup to be a self._gpio.INPUT before this is called
	def _read(self, pin):
		return self._gpio.digitalRead(pin)

	# ait is assumed that the pin was setup to be a self._gpio.ANALOG_INPUT before this is called
	def _analogRead(self, pin):
		return self._gpio.analogRead(pin)

	def exitGracefully(self):
		super(EdisonGPIODriver, self).exitGracefully()
		self._gpio.cleanup()

if __name__ = '__main__':
	from multiprocessing import Manager
	from multiprocessing import Queue
	import time
	m = Manager
	q = m.Queue()
	e = EdisonGPIODriver(q, (,))
	q.put(["setup", [7, 8], ["OUTPUT", "OUTPUT"]])
	q.put(["setup", 5, "PWM"])
	q.put(["setupPWM", 5, 60])
	q.put(["write", [7, 8], [0,1]])
	q.put(["setDC", 5, 50])
	time.sleep(5)
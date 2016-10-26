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
		OUTPUT = self._gpio.OUT
		INPUT = self._gpio.IN
		PWM = self._gpio.PWM
		ANALOG_INPUT = self._gpio.ANALOG_INPUT

	# args should be tuples
	def setup(self, pins, modes):
		for i in range(0, len(pins)):
			if modes[i] == 'INPUT':
				self._gpio.pinMode(pins[i], self.INPUT)
			elif modes[i] == 'OUTPUT':
				self._gpio.pineMode(pins[i], self.OUTPUT)
			elif modes[i] == 'ANALOG_INPUT':
				self._gpio.pinMode(pins[i], self.ANALOG_INPUT)

	# args should be tuples
	def setupPWM(self, pins, frequencies):
		for i in range(0, len(pins)):
			self._gpio.pinMode(pins[i], self._gpio.PWM)
			self._gpio.setPWMPeriod(pins[i], 1.0/frequencies[i])
			self._gpio.analogWrite(pins[i], 0)

	# args should be tuples
	# it is assumed that the entries of pins are already setup as PWM outputs
	def changeFrequency(self, pins, frequencies):
		for i in range(0, len(pins)):
			self._gpio.setPWMPeriod(pins[i], 1.0/frequencies[i])

	# args should be tuples
	# it is assumed that the entries of pins are already setup as PWM outputs
	def setDC(self, pins, values):
		for i in range(0, len(pins)):
			if values[i] >= 0 and values[i] <= 100:
				# transform is done because analogWrite has a range from 0-100 for duty cycle values
				self._gpio.analogWrite(pins[i], util.transform(values[i], 0, 100, 0, 255))
			else:
				print "Incorrect duty cycle value was provided"

	# args should be tuples
	# it is assumed that the pins are already setup to be outputs
	def write(self, pins, levels):
		for i in range(0, len(pins)):
			self._gpio.digitalWrite(pins[i], levels[i])

	# ait is assumed that the pin was setup to be a self._gpio.INPUT before this is called
	def _read(self, pin):
		return self._gpio.digitalRead(pin)

	# ait is assumed that the pin was setup to be a self._gpio.ANALOG_INPUT before this is called
	def _analogRead(self, pin):
		return self._gpio.analogRead(pin)

	def exitGracefully(self):
		super(EdisonGPIODriver, self).exitGracefully()
		self._gpio.cleanup()
#!/usr/bin/env python

from GPIOBaseClass import GPIOBaseClass
import mraa
import sys, os

class EdisonGPIODriver(GPIOBaseClass):
	OUTPUT = mraa.DIR_OUT
	INPUT = mraa.DIR_IN
	PWM = ""
	ANALOG_INPUT = ""
	gpioDict = {}
	pwmDict = {}

	def __init__(self, encoderPins):
		super(EdisonGPIODriver, self).__init__(encoderPins)

	# args should be tuples, list, or a single int
	def setup(self, pins, modes):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				if modes[i] == 'INPUT':
					self.gpioDict[pins[i]] = mraa.Gpio(pins[i])
					self.gpioDict[pins[i]].dir(self.INPUT)
				elif modes[i] == 'OUTPUT':
					self.gpioDict[pins[i]] = mraa.Gpio(pins[i])
					self.gpioDict[pins[i]].dir(self.OUTPUT)
				elif modes[i] == 'ANALOG_INPUT':
					pass
				elif modes[i] == 'PWM':
					self.setupPWM(pins[i], 60)
		else:
			if modes[i] == 'INPUT':
				self.gpioDict[pins] = mraa.Gpio(pins)
				self.gpioDict[pins].dir(self.INPUT)
			elif modes[i] == 'OUTPUT':
				self.gpioDict[pins] = mraa.Gpio(pins)
				self.gpioDict[pins].dir(self.OUTPUT)
			elif modes == 'ANALOG_INPUT':
				pass
			elif modes == 'PWM':
				self.setupPWM(pins, 60)

	# args should be tuples, lists, or a single int
	def setupPWM(self, pins, frequencies):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				self.pwmDict[pins[i]] = [mraa.Pwm(pins[i]), False]
				self.pwmDict[pins[i]][0].period(1.0/frequencies[i])
		else: # must be an int
			self.pwmDict[pins] = [mraa.Pwm(pins), False]		
			self.pwmDict[pins][0].period(1.0/frequencies)

	# args should be tuples, lists, or a single int
	# it is assumed that the entries of pins are already setup as PWM outputs
	def changeFrequency(self, pins, frequencies):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				self.pwmDict[pins[i]][0].period(1.0/frequencies[i])
		else: # must be an int
			self.pwmDict[pins][0].period(1.0/frequencies)

	# args should be tuples, lists, or a single int
	# it is assumed that the entries of pins are already setup as PWM outputs
	def setDC(self, pins, values):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				if values[i] >= 0 and values[i] <= 100:
					if values[i] != 0:
						if not self.pwmDict[pins[i]][1]:
							self.pwmDict[pins[i]][0].enable(True)
							self.pwmDict[pins[i]][1] = True
						self.pwmDict[pins[i]][0].write(values[i]/100.0)
					else:
						self.pwmDict[pins[i]][0].write(0)
						self.pwmDict[pins[i]][0].enable(False)
						self.pwmDict[pins[i]][1] = False
				else:
					print "Incorrect duty cycle value was provided"
		else: # mut be an int
			if values >- 0 and values <= 100:
				if values != 0:
					if not self.pwmDict[pins][1]:
						self.pwmDict[pins][0].enable(True)
						self.pwmDict[pins][1] = True
					self.pwmDict[pins][0].write(values/100.0)
				else:
					self.pwmDict[pins][0].write(0)
					self.pwmDict[pins][0].enable(False)
					self.pwmDict[pins][1] = False

	# args should be tuples, lists, or a single int
	# it is assumed that the pins are already setup to be outputs
	def write(self, pins, levels):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				self.gpioDict[pins[i]].write(levels[i])
		else: # must be an int
			self.gpioDict[pins].write(levels)

	def setupWaitForEdgeISR(self, callback, pin):
		g = mraa.Gpio(pin)
		g.dir(self.INPUT)
		mraa.isr(g, mraa.EDGE_BOTH, callback)

	# ait is assumed that the pin was setup to be a self._gpio.INPUT before this is called
	def _read(self, pin):
		return self.gpioDict[pin].read()

	# ait is assumed that the pin was setup to be a self._gpio.ANALOG_INPUT before this is called
	def _analogRead(self, pin):
		pass

	def exitGracefully(self):
		super(EdisonGPIODriver, self).exitGracefully()

if __name__ == '__main__':
	from multiprocessing import Manager
	from multiprocessing import Queue
	import time
	m = Manager
	q = m.Queue()
	e = EdisonGPIODriver(q, ())
	q.put(["setup", [7, 8], ["OUTPUT", "OUTPUT"]])
	q.put(["setup", 5, "PWM"])
	q.put(["setupPWM", 5, 60])
	q.put(["write", [7, 8], [0,1]])
	q.put(["setDC", 5, 50])
	time.sleep(5)

#!/usr/bin/env python

from GPIOBaseClass import GPIOBaseClass
import RPi.GPIO as GPIO

# remember this is a Process
class RPiGPIODriver(GPIOBaseClass):
	OUTPUT = GPIO.OUT
	INPUT = GPIO.IN
	PWM = GPIO.OUT
	ANALOG_INPUT = "Raspberry pi doesn't have analog in"

	# dictionary of pins and pwmObjs
	# _pwmObjs is of the form {pin: (pwmObj, pwmStarted), ...}
	_pwmObjs = {}

	def __init__(self, commandQueue, responsePipes):
		super(RPiGPIODriver, self).__init__(commandQueue, responsePipes)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setwarnings(False)

	# args should be tuples, lists, or a single ints
	def setup(self, pins, modes):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				if modes[i] == 'INPUT':
					GPIO.setup(pins[i], self.INPUT, pull_up_down=GPIO.PUD_DOWN)
				elif modes[i] == 'OUTPUT' or modes[i] == 'PWM':
					GPIO.setup(pins[i], self.OUTPUT)
				elif modes[i] == 'ANALOG_INPUT':
					GPIO.setup(pins[i], self.ANALOG_INPUT)
		else: # must be ints
			if modes == 'INPUT':
				GPIO.setup(pins, self.INPUT, pull_up_down=GPIO.PUD_DOWN)
			elif modes == 'OUTPUT' or modes == 'PWM':
				GPIO.setup(pins, self.OUTPUT)
			elif modes == 'ANALOG_INPUT':
				GPIO.setup(pins, self.ANALOG_INPUT)

	# args should be tuples, lists, or a single ints
	def setupPWM(self, pins, frequencies):
		if type(pins) is list or type(pins) is tuple:
			# create a pwmObj for every pin in pins that does not have one associated with it
			for i in range(0, len(pins)):
				if not pins[i] in self._pwmObjs:
					self._pwmObjs[pins[i]] = [GPIO.PWM(pins[i], frequencies[i]), False]
		else: # must be ints
			if not pins in self._pwmObjs:
				self._pwmObjs[pins] = [GPIO.PWM(pins, frequencies), False]

	# args should be tuples, lists, or a single ints
	def changeFrequency(self, pins, frequencies):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				# highly frowned upon if trying to change frequency of a pwm obj that hasn't been made yet
				# yet still acceptable, but is redundant and slow
				if not pins[i] in self._pwmObjs:
					self.setupPWM(pins[i], frequencies[i])
				else:
					self._pwmObjs[pins[i]][0].ChangeFrequency(frequencies[i])
		else: # must be ints
			if not pins in self._pwmObjs:
				self.setupPWM(pins, frequencies)
			else:
				self._pwmObjs[pins][0].ChangeFrequency(frequencies)

	# args should be tuples, lists, or a single ints
	def setDC(self, pins, values):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				if pins[i] in self._pwmObjs:
					if values[i] == 0:
						self._pwmObjs[pins[i]][0].stop()
						self._pwmObjs[pins[i]][1] = False
					# if values[i] is valid
					elif values[i] > 0 and values[i] <= 100:
						# if pwm is active/not stopped/ started
						if self._pwmObjs[pins[i]][1]:
							self._pwmObjs[pins[i]][0].ChangeDutyCycle(values[i])
						else:
							self._pwmObjs[pins[i]][0].start(values[i])
							self._pwmObjs[pins[i]][1] = True
					else:
						print "Incorrect duty cycle value was provided"
				else:
					print "Process tried to set pin that was not setup as a PWM pin to have a duty cycle"
		else: # must be ints
			if pins in self._pwmObjs:
				if values == 0:
					self._pwmObjs[pins][0].stop()
					self._pwmObjs[pins][1] = False
				# if values is valid
				elif values > 0 and values <= 100:
					# if pwm is active/not stopped/ started
					if self._pwmObjs[pins][1]:
						self._pwmObjs[pins][0].ChangeDutyCycle(values)
					else:
						self._pwmObjs[pins][0].start(values)
						self._pwmObjs[pins][1] = True
				else:
					print "Incorrect duty cycle value was provided"
			else:
				print "Process tried to set pin that was not setup as a PWM pin to have a duty cycle"

	# args should be tuples, lists, or a single ints
	# it is assumed that the pins are already setup to be outputs
	def write(self, pins, levels):
		if type(pins) is list or type(pins) is tuple:
			for i in range(0, len(pins)):
				GPIO.output(pins[i], levels[i])
		else: # must be ints
			GPIO.output(pins, levels)

	# it is assumed that the pin is already setup
	def setupWaitForEdgeISR(self, callback, pin):
		GPIO.add_event_detect(pin, GPIO.BOTH, callback=callback)

	# it is assumed that pin is setup to be GPIO.INPUT
	def _read(self, pin):
		return GPIO.input(pin)

	def _analogRead(self, pin):
		print ANALOG_INPUT
		return -1

	def exitGracefully(self):
		super(RPiGPIODriver, self).exitGracefully()
		GPIO.cleanup()

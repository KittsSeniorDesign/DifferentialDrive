#!/usr/bin/env python
from wiringx86 import GPIOEdison as GPIO
import mraa
import time

# Warning, untested
class EdisonL298Driver:
	gpio = None
	pwmPin = [5, 6]
	dirPin = [[7, 8], [10, 9]] # TODO possible pull these from config.txt

	pwmObj = [None, None]
	# flag for motors pwmObj is started
	freq = 60#Hertz
	maxDC = 100
	minDC = 20

	def __init__(self):
		self.setupPins()
		self.initializePWM()

	def setupPins(self):
		self.gpio = GPIO(debug=False)
		for i in range(0, 2):
			#self.gpio.pinMode(self.pwmPin[i], self.gpio.OUTPUT)
			for j in range(0, 2):
				self.gpio.pinMode(self.dirPin[i][j], self.gpio.OUTPUT)

	def initializePWM(self): 
		for i in range(0 ,2):
			self.setDirectionPins([0,0])
		for i in range(0, 2):
			self.pwmObj[i] = mraa.Pwm(self.pwmPin[i])
			self.pwmObj[i].period(1.0/60)
                        self.pwmObj[i].pulsewidth(0)
			self.pwmObj[i].enable(True)

	def setDirectionPins(self, direction):
		for i in range(0, 2):
			if direction[i] == 1:
				self.gpio.digitalWrite(self.dirPin[i][0], self.gpio.HIGH)
				self.gpio.digitalWrite(self.dirPin[i][1], self.gpio.LOW)
			else:
				self.gpio.digitalWrite(self.dirPin[i][0], self.gpio.LOW)
				self.gpio.digitalWrite(self.dirPin[i][1], self.gpio.HIGH)

	# set PWM duty cycle
	# 0 <= powers <= 100
	# powers should be an array with 2 indexes [mLeftPower, mRightPower]
	# direction should be an array with 2 indexes [mLeftDir, mRightDir]
	def setDC(self, powers, direction):
		for i in range(0 ,2):
			self.setDirectionPins(direction)
		for i in range(0, 2):
			self.pwmObj[i].pulsewidth(0.0166666666666667*(powers[i]/100.0))

	def exitGracefully(self):
		for i in range(0, 2):
			if self.pwmObj[i]:
				self.pwmObj[i].pulsewidth(0)
				self.pwmObj[i].enable(False)
		self.gpio.cleanup()

if __name__ == "__main__":
	e = EdisonL298Driver()
	for i in range(0, 2):
		e.setDC([50, 50], [0, 0])
		time.sleep(1)
		e.setDirectionPins([1, 1])
		time.sleep(1)
		e.setDirectionPins([0, 1])
		time.sleep(1)
		e.setDirectionPins([1, 0])
		time.sleep(1)
		e.setDirectionPins([0, 0])
		time.sleep(1)
		e.setDC([0, 0], [0, 0])
		time.sleep(1)

	e.setDC([0, 0], [0, 0])
        e.exitGracefully()

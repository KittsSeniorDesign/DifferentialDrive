from wiringx86 import GPIOEdison as GPIO
import time

class EdisonEncoder:
	pin = None
	timeout = 100
	gpio = None

	def __init__(self):
		self.gpio = GPIO(debug=False)

	def setupPin(self, pin):
		self.pin = pin
		self.gpio.pinMode(pin, self.gpio.INPUT)

	# loop until pin changes from low to high or high to low or timeout
	def waitForEdge(self):
		starttime = time.time()
		initLevel = self.gpio.digitalRead(self.pin)
		while time.time()-starttime < self.timeout and self.gpio.digitalRead(self.pin) == initLevel:
			pass
		return self.pin

	def exitGracefully(self):
		self.gpio.cleanup()
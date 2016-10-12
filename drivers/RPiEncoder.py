import RPi.GPIO as GPIO

class RPiEncoder:
	pin = None
	timeout = 100

	def __init__(self):
		GPIO.setmode(GPIO.BOARD)

	def setupPin(self, pin):
		self.pin = pin
		GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

	def waitForEdge(self):
		return GPIO.wait_for_edge(self.pin, GPIO.BOTH, timeout=self.timeout)

	def exitGracefully(self):
		GPIO.cleanup()
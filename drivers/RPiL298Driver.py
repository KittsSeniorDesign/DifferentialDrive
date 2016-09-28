import RPi.GPIO as GPIO

class RPiL298Driver: #TODO make this extend a driver class with abstract methods setDC() and setDirectionPins()

	pwmPin = [38, 37]
	# assuming you're using a L298n and a rpi
	dirPin = [[31,32], [35,33]]

	pwmObj = [None, None]
	# flag for motors pwmObj is started
	pwmStarted = [False, False]
	freq = 60#Hertz
	maxDC = 100
	minDC = 20

	def __init__(self):
		self.setupPins()
		self.initializePWM()

	def setupPins(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setwarnings(False)
		for i in range(0, 2):
			GPIO.setup(self.pwmPin[i], GPIO.OUT)
			for j in range(0, 2):
				GPIO.setup(self.dirPin[i][j], GPIO.OUT)

	def initializePWM(self):
		for i in range(0 ,2):
			self.setDirectionPins([0,0])
		for i in range(0, 2):
			self.pwmObj[i] = GPIO.PWM(self.pwmPin[i], self.freq)
			self.pwmStarted[i] = False

	def setDirectionPins(self, direction):
		for i in range(0, 2):
			if direction[i]:
				GPIO.output(self.dirPin[i][0], GPIO.HIGH)
				GPIO.output(self.dirPin[i][1], GPIO.LOW)
			else:
				GPIO.output(self.dirPin[i][0], GPIO.LOW)
				GPIO.output(self.dirPin[i][1], GPIO.HIGH)

	# set PWM duty cycle
	# powers should be an array with 2 indexes [mLeftPower, mRightPower]
	# direction should be an array with 2 indexes [mLeftDir, mRightDir]
	def setDC(self, powers, direction):
		for i in range(0 ,2):
			self.setDirectionPins(direction)
		for i in range(0, 2):
			if powers[i] == 0:
				self.pwmObj[i].stop()
				self.pwmStarted[i] = False
			else:
				if self.pwmStarted[i]:
					self.pwmObj[i].ChangeDutyCycle(powers[i])
				else:
					self.pwmObj[i].start(powers[i])
					self.pwmStarted[i] = True			

	def exitGracefully(self):
		for i in range(0, 2):
			if self.pwmObj[i]:
				self.pwmObj[i].ChangeDutyCycle(0)
				self.pwmObj[i].stop()
		GPIO.cleanup()
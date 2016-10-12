from wiringx86 import GPIOEdison as GPIO
import mraa

# Warning, untested
class EdisonL298Driver:
	gpio = None
	pwmPin = [5, 6]
	dirPin = [[7,8], [9,10]] # TODO possible pull these from config.txt

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
			self.pwmObj[i].period(1/60)
			self.pwmObj[i].enable(False)
			self.pwmStarted[i] = False

	def setDirectionPins(self, direction):
		for i in range(0, 2):
                        print direction[i] 
			if direction[i]:
                                print "arg"
				self.gpio.digitalWrite(self.dirPin[i][0], self.gpio.HIGH)
                                print "dirt"
				self.gpio.digitalWrite(self.dirPin[i][1], self.gpio.LOW)
                                print "que?"
			else:
                                print "0arg"
				self.gpio.digitalWrite(self.dirPin[i][0], self.gpio.LOW)
                                print "0dirt"
				self.gpio.digitalWrite(self.dirPin[i][1], self.gpio.HIGH)
                                print "0que?"

	# set PWM duty cycle
	# 0 <= powers <= 100
	# powers should be an array with 2 indexes [mLeftPower, mRightPower]
	# direction should be an array with 2 indexes [mLeftDir, mRightDir]
	def setDC(self, powers, direction):
		for i in range(0 ,2):
			self.setDirectionPins(direction)
		for i in range(0, 2):
			if powers[i] == 0:
				self.pwmObj[i].enable(False)
				self.pwmStarted[i] = False
			else:
				if self.pwmStarted[i]:
					# (1/60)*(power/100) to get duty cycle
					self.pwmObj[i].pulsewidth(0.0166666666666667*(powers[i]/100))
				else:
					# (1/60)*(power/100) to get duty cycle
					self.pwmObj[i].pulsewidth(0.0166666666666667*(powers[i]/100))
					self.pwmObj[i].enable(True)
					self.pwmStarted[i] = True			

	def exitGracefully(self):
		for i in range(0, 2):
			if self.pwmObj[i]:
				self.pwmObj[i].pulsewidth(0)
				self.pwmObj[i].enable(False)
				self.pwmStarted[i] = False
		self.gpio.cleanup()

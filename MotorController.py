#!/usr/bin/env python

# This file was created by Ryan Cooper in 2016 for a Raspberry Pi
# This class controls the motors for the robot which are configured as 
# a differential drive, this code is written for a raspberry pi, 
# TODO but should be reworked to load a driver that drives the motors
import RPi.GPIO as GPIO
import time
import sys
import math

from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Pipe

import util

class MotorController(Process):
	# possible states
	STEERING_THROTTLE_OFFBOARD = 1
	STEERING_THROTTLE_ONBOARD = 2
	TANK = 3
	VELOCITY_HEADING = 4
	state = STEERING_THROTTLE_OFFBOARD

	# possible velocity heading states
	TURNING = 0
	DRIVING = 1
	# velocity heading state
	vhState = TURNING

	LEFT = 0
	RIGHT = 1

	pwmPin = [38, 37]
	# assuming you're using a L298n and a rpi
	dirPin = [[31,32], [35,33]]

	pwmObj = [None, None]
	# flag for motors pwmObj is started
	pwmStarted = [False, False]
	freq = 60#Hertz
	maxDC = 100
	minDC = 20
	mPowers = [0, 0]
	direction = [0, 0]	# forward or backward
	# set by time.time(), used to stop bot when dced
	lastQueue = 0
	go = True
	# only consumes the queue
	encQueue = None
	controllerQueue = None
	# used to shut the process down
	pipe = None

	# for vel/heading mode
	desiredHeading = 0
	desiredVel = 0
	currentHeading = 0

	def __init__(self, *args, **kwargs):
		super(MotorController, self).__init__()
		for key in kwargs:
			if key == 'encQueue':
				self.encQueue = kwargs[key]
			elif key == 'pipe':
				self.pipe = kwargs[key]
			elif key == 'controllerQueue':
				self.controllerQueue = kwargs[key]
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
			self.setDirectionPins()
		for i in range(0, 2):
			self.pwmObj[i] = GPIO.PWM(self.pwmPin[i], self.freq)
			self.pwmStarted[i] = False

	def setDirectionPins(self):
		for i in range(0, 2):
			if self.direction[i]:
				GPIO.output(self.dirPin[i][0], GPIO.HIGH)
				GPIO.output(self.dirPin[i][1], GPIO.LOW)
			else:
				GPIO.output(self.dirPin[i][0], GPIO.LOW)
				GPIO.output(self.dirPin[i][1], GPIO.HIGH)

	# set PWM duty cycle
	def setDC(self):
		for i in range(0 ,2):
			self.setDirectionPins()
		for i in range(0, 2):
			if self.mPowers[i] == 0:
				self.pwmObj[i].stop()
				self.pwmStarted[i] = False
			else:
				if self.pwmStarted[i]:
					self.pwmObj[i].ChangeDutyCycle(self.mPowers[i])
				else:
					self.pwmObj[i].start(self.mPowers[i])
					self.pwmStarted[i] = True

	# vel in m/s
	def setDCByVel(self, vel):
		if vel > 0:
			self.direction = [0, 0]
		else:
			self.direction = [1, 1]
		if abs(vel) > util.maxVel:
			self.mPowers[i] = maxDC
		elif abs(vel) < util.minVel:
			self.mPowers[i] = 0
		else:
			 # experimenal, play with minDC, and minVel because maxVel was observerd at maxDC
			self.mPowers[i] = util.transform(vel, util.minVel, util.maxVel, self.minDC, self.maxDC)
		self.setDC()

	def exitGracefully(self):
		for i in range(0, 2):
			if self.pwmObj[i]:
				self.pwmObj[i].ChangeDutyCycle(0)
				self.pwmObj[i].stop()
		GPIO.cleanup()
		self.go = False

	def steeringThrottle(self, data):
		steering = util.transform(data[1], 1000 , 2000, -1, 1)
		throttle = util.transform(data[2], 1000, 2000, -1, 1)
		maxSm = 35
		maxSp = 220
		maxMove = 220
		minMove = 0
		sm = util.transform(abs(steering), 0, 1, 0, maxSm)
		sp = util.transform(abs(steering), 0, 1, 0, maxSp)
		t = util.transform(abs(throttle), 0, 1, minMove, maxMove)
		L = t
		R = t
		end = 1500
		if throttle < 0:
			if steering < 0:
				L += sm
				R -= sp
			else:
				L -= sp
				R += sm
			end = 2000
		else:
			if steering < 0:
				L -= sp
				R += sm
			else:
				L += sm
				R -= sp
			end = 1000
		mL = util.transform(util.clampToRange(L, 0, 255), 0, 255, 1500, end)
		mR = util.transform(util.clampToRange(R, 0, 255), 0, 255, 1500, end)
		self.changeMotorVals(mL, mR)

	# this function will consume the controllerQueue, which was filled by DDMCServer
	# and will change the motors powers and directions according to what was in the queue
	# it also will monitor that the bot is still receiving commands, and if it isn't, it will stop the bot
	def handleControllerQueue(self):
		print self.state
		# if there hasn't been anything in the queue in half a second
		if time.time()-self.lastQueue > .5 and self.controllerQueue.empty():
			# stop the bot
			self.direction = [0, 0]
			self.mPowers = [0, 0]
			self.lastQueue = time.time()
		else:
			while not self.controllerQueue.empty(): # this is a while so that the most recent thing in the queue is the resultant command that is done
				good = True
				try:
					# nowait because this process was called from the main loop which controls the motors
					# so we don't want this function to block.
					data = self.controllerQueue.get_nowait()
				except Queue.Empty as msg: 
					# realistically this should never happen because we check to see that the queue is not empty
					# but it is shared memory, and who knows?
					good = False
				if good:
					mL = 1500
					mR = 1500
					if data[0] == self.STEERING_THROTTLE_OFFBOARD or data[0] == self.TANK: # recieved motor level commands
						self.state = data[0]
						mL = data[1]
						mR = data[2]
						self.changeMotorVals(mL, mR)
					elif data[0] == self.STEERING_THROTTLE_ONBOARD: # recieved joystick information (throttle, steering)
						self.state = data[0]
						self.steeringThrottle(data)# this calls changeMotorVals()
					elif data[0] == self.VELOCITY_HEADING:
						self.state = data[0]
						self.vhState = self.TURNING
						self.desiredVel = data[1]
						self.desiredHeading = data[2]
						self.goToHeading(self.desiredHeading)
				self.lastQueue = time.time()

	# this sets up the values used to drive the motors 
	# it does not drive the motor because this function is tied to the queue
	# and only gets executed when something is in the queue
	# yet we want the motors to be constantly receiving contol information
	# 1000 <= mL,mR <= 2000, 1500 means the wheels wont turn
	def changeMotorVals(self, mL, mR):
		if mL > 1500:
			self.direction[self.LEFT] = 1
			self.mPowers[self.LEFT] = util.clampToRange(util.transform(mL, 1500, 2000, 0, 100), self.minDC-1, self.maxDC)
		else:
			self.direction[self.LEFT] = 0
			self.mPowers[self.LEFT] = util.clampToRange(util.transform(mL, 1500, 1000, 0, 100), self.minDC-1, self.maxDC)
		if self.mPowers[self.LEFT] < self.minDC:
			self.mPowers[self.LEFT] = 0

		if mR > 1500:
			self.direction[self.RIGHT] = 0
			self.mPowers[self.RIGHT] = util.clampToRange(util.transform(mR, 1500, 2000, 0, 100), self.minDC-1, self.maxDC)
		else :
			self.direction[self.RIGHT] = 1
			self.mPowers[self.RIGHT] = util.clampToRange(util.transform(mR, 1500, 1000, 0, 100), self.minDC-1, self.maxDC)
		if self.mPowers[self.RIGHT] < self.minDC:
			self.mPowers[self.RIGHT] = 0
		print self.mPowers

		if self.state != self.VELOCITY_HEADING:
			self.setDC()

	def goToHeading(self, h):
		if h > 2*math.pi:
			# make h < 2pi
			h = h-(2*math.pi*math.floor(h/(2*math.pi)))
		elif h < -2*math.pi:
			# make h > -2pi
			h = h+(2*math.pi*math.floor(h/(2*math.pi)))
		angDiff = h-self.currentHeading
		if angDiff > math.pi:
			angDiff = abs(angDiff-2*math.pi)
			self.direction = [1, 0]
		else:
			self.direction = [0, 1]
		#	angle*radius=arclen
		dist = angDiff*util.botWidth/2
		self.requiredCounts = round(dist/util.distPerBlip)
		self.mPowers = [75, 75]
		self.setDC()

	# PID part of the wheel controller loop
	def controlPowers(self, data):	#TODO possible use mm/sec instead of m/s because it will be more accurate because floating point is bad
		aveVel = util.distPerBlip*data[2]
		print aveVel
		p = self.desiredVel-aveVel
		pPWM = 0
		if abs(p) >= util.minVel:
			if p > 0:
				pPWM = util.transform(vel, util.minVel, util.maxVel, self.minDC, self.maxDC)
			else:
				pPWM = -util.transform(vel, util.minVel, util.maxVel, self.minDC, self.maxDC)
		if(data[0] == util.leftEncPin):
			self.mPowers[self.LEFT] += pPWM
		elif(data[0] == util.rightEncPin):
			self.mPowers[self.RIGHT] += pPWM
		else:
			print "Encoder is reading data to an unexpected pin"
		self.setDC()

	def handleEncoderQueue(self):	#TODO
		while not self.encQueue.empty():	
			good = True
			try: 
				# nowait because this process was called from the main loop which controls the motors
				# so we don't want this function to block.
				data = self.encQueue.get_nowait()
			except Queue.Empty as msg:
				# realistically this should never happen because we check to see that the queue is not empty
				# but it is shared memory, and who knows?
				good = False
			if good:
				if self.vhState == self.TURNING:
					# note, does not check which motor moved the desired amount, possible change this
					if data[1] >= self.requiredCounts:
						self.vhState = self.DRIVING
						self.setDCByVel(self.desiredVel)
				else:
					# calls setDC()
					# pid part of the loop
					self.controlPowers(data)

	# check to see if the process should stop
	def checkIfShouldStop(self):
		if self.pipe.poll():
			data = self.pipe.recv()
			if (not data == None) and 'stop' in data:
				self.go = False
				self.pipe.close()

	def run(self):
		self.go = True
		try:
			while self.go:
			#	print self.mPowers
			#	print self.direction
				self.handleControllerQueue()
				self.handleEncoderQueue()
				self.checkIfShouldStop()
				time.sleep(.01)
			self.exitGracefully()
		except Exception as msg:
			print msg
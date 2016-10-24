#!/usr/bin/env python

# This file was created by Ryan Cooper in 2016 for a Raspberry Pi
# This class controls the motors for the robot which are configured as 
# a differential drive, this code is written for a raspberry pi, 
# TODO but should be reworked to load a driver that drives the motors
import time
import sys
import math

from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Pipe

import util

#WARNING: calling print too frequently will cause high latency from control input to reaction

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
	# the class that will control the motors depending on what platform this code is running on
	driver = None

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
	#list used to reset the counts of the encoders
	encPipes = None

	# for vel/heading mode
	desiredHeading = 0
	# should be in mm/sec
	desiredVel = 0
	currentHeading = 0
	requiredCounts = 0

	def __init__(self, *args, **kwargs):
		super(MotorController, self).__init__()
		for key in kwargs:
			if key == 'encQueue':
				self.encQueue = kwargs[key]
			elif key == 'encPipes':
				self.encPipes = kwargs[key]
			elif key == 'pipe':
				self.pipe = kwargs[key]
			elif key == 'controllerQueue':
				self.controllerQueue = kwargs[key]
			elif key == 'driver':
				self.driver = kwargs[key]()
                self.driver.setDC([0,0],[1,1])

	# vel in m/s
	def setDCByVel(self, vel):
		if vel > 0:
			self.direction = [0, 0]
		else:
			self.direction = [1, 1]
		for i in range(0, 2):
			if abs(vel) > util.maxVel:
				self.mPowers[i] = self.driver.maxDC
			elif abs(vel) < util.minVel:
				self.mPowers[i] = 0
			else:
				 # experimenal, play with minDC, and minVel because maxVel was observerd at maxDC
				self.mPowers[i] = util.transform(vel, util.minVel, util.maxVel, self.driver.minDC, self.driver.maxDC)
		self.driver.setDC(self.mPowers,self.direction)

	def exitGracefully(self):
		self.driver.exitGracefully()

	def steeringThrottle(self, data):
		steering = util.transform(data[1], 1000, 2000, -1, 1)
		throttle = util.transform(data[2], 1000, 2000, -1, 1)
		# used in steering to change motor velocities 
		maxSp = 35 
		maxSm = 220
		# max possible speed when moving forward
		maxMove = 220
		minMove = 0
		# sp is what will get added (plus) to t (which is the throttle value)
		sp = util.transform(abs(steering), 0, 1, 0, maxSp)
		# sm is what will get subtracted (minus) to t (which is the throttle value)
		sm = util.transform(abs(steering), 0, 1, 0, maxSm)
		t = util.transform(abs(throttle), 0, 1, minMove, maxMove)
		L = t
		R = t
		end = 1500
		if throttle < 0:
			if steering < 0:
				# right motor should slow down, left motor should speed up
				L += sp
				R -= sm
			else:
				# left motor should slow down, right motor should speed up
				L -= sm
				R += sp
			end = 2000
		else:
			if steering < 0:
				# left motor should slow down, right motor should speed up
				L -= sm
				R += sp
			else:
				# right motor should slow down, left motor should speed up
				L += sp
				R -= sm
			end = 1000
		mL = util.transform(util.clampToRange(L, 0, 255), 0, 255, 1500, end)
		mR = util.transform(util.clampToRange(R, 0, 255), 0, 255, 1500, end)
		self.changeMotorVals(mL, mR)

	# this function will consume the controllerQueue, which was filled by DDMCServer
	# and will change the motors powers and directions according to what was in the queue
	# it also will monitor that the bot is still receiving commands, and if it isn't, it will stop the bot
	def handleControllerQueue(self):
		#print self.state
		# if there hasn't been anything in the queue in half a second
		if self.state != self.VELOCITY_HEADING and time.time()-self.lastQueue > .5 and self.controllerQueue.empty():
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
			self.mPowers[self.LEFT] = util.clampToRange(util.transform(mL, 1500, 2000, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		else:
			self.direction[self.LEFT] = 0
			self.mPowers[self.LEFT] = util.clampToRange(util.transform(mL, 1500, 1000, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		if self.mPowers[self.LEFT] < self.driver.minDC:
			self.mPowers[self.LEFT] = 0

		if mR > 1500:
			self.direction[self.RIGHT] = 1
			self.mPowers[self.RIGHT] = util.clampToRange(util.transform(mR, 1500, 2000, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		else :
			self.direction[self.RIGHT] = 0
			self.mPowers[self.RIGHT] = util.clampToRange(util.transform(mR, 1500, 1000, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		if self.mPowers[self.RIGHT] < self.driver.minDC:
			self.mPowers[self.RIGHT] = 0
		#print self.mPowers

		if self.state != self.VELOCITY_HEADING:
			self.driver.setDC(self.mPowers,self.direction)
		# VELOCITY_HEADING mode calls setDC from either goToHeading, or setDCbyVel

	def goToHeading(self, h):
		if abs(self.currentHeading-h) > .01:
			if h > 2*math.pi:
				# make h < 2pi
				h = h-(2*math.pi*math.floor(h/(2*math.pi)))
			elif h < -2*math.pi:
				# make h > -2pi
				h = h+(2*math.pi*math.floor(h/(2*math.pi)))
			angDiff = h-self.currentHeading
			self.changeHeadingByRadians(angDiff)

	def changeHeadingByRadians(self, h):
		if abs(h) > .01:
			self.resetEncoders()
			if h > 0:
				self.direction = [1, 0]
			else:
				self.direction = [0, 1]
			#	angle*radius=arclen
			sys.stdout.write("Moving by radians: ")
			sys.stdout.write(str(h))
			dist = h*util.botWidth/2
			self.requiredCounts = abs(dist/util.distPerBlip)
			sys.stdout.write(" requiredCounts ")
			print self.requiredCounts
			self.mPowers = [75, 75]
			self.driver.setDC(self.mPowers,self.direction)

	def resetEncoders(self):
		for p in self.encPipes:
			p.send('reset')

	# PID part of the wheel controller loop
	def controlPowers(self, vel):	#TODO possible use mm/sec instead of m/s because it will be more accurate because floating point is bad
		if self.desiredVel != 0:
			p = self.desiredVel-vel
			pPWM = 0
			if abs(p) >= util.minVel:
				if p > 0:
					pPWM = util.transform(vel, util.minVel, util.maxVel, self.driver.minDC, self.driver.maxDC)
				else:
					pPWM = -util.transform(vel, util.minVel, util.maxVel, self.driver.minDC, self.driver.maxDC)
			if(data[0] == util.leftEncPin):
				self.mPowers[self.LEFT] = util.clampToRange(self.mPowers[self.LEFT]+pPWM, 0, 100)
			elif(data[0] == util.rightEncPin):
				self.mPowers[self.RIGHT] = util.clampToRange(self.mPowers[self.RIGHT]+pPWM, 0, 100)
			else:
				print "Encoder is reading data to an unexpected pin"
		else:
			self.mPowers = [0, 0]
		self.driver.setDC(self.mPowers,self.direction)

	def handleEncoderQueue(self):	
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
			if good and self.state == self.VELOCITY_HEADING:
				if self.vhState == self.TURNING:
					# note, does not check which motor moved the desired amount, possible change this
					print data
					if data[1] >= self.requiredCounts:
						print "dirt"
						self.vhState = self.DRIVING
						self.currentHeading = self.desiredHeading
						self.setDCByVel(self.desiredVel)
				else:
					# data[2] = seconds/blip
					# convert to rotations per second 
					# then multiply by distance wheel travels in one rotation
					# result is mm/second
					vel = 0
					if data[2] != 0:
						vel = util.circumferenceOfWheel*util.stateChangesPerRevolution/data[2]
					# calls setDC()
					# pid part of the loop
					self.controlPowers(data[2])

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
			print "Motor controller"
			print msg

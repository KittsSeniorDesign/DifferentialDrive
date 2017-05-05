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
	WAYPOINT = 5
	ENCODER_TEST = 6
	state = STEERING_THROTTLE_OFFBOARD

	# possible velocity heading states
	TURNING = 0
	DRIVING = 1
	# velocity heading state
	vhState = TURNING

	LEFT = 0
	RIGHT = 1

	mPowers = [0, 0]
	direction = [0, 0]	# forward or backward
	# set by time.time(), used to stop bot when dced
	lastQueue = 0
	go = True

	# for vel/heading mode
	desiredHeading = 0
	# should be in mm/sec
	desiredVel = 0
	currentHeading = 0
	requiredCounts = 0

	motorOffValue = 1024
	motorHighValue = 2048
	motorLowValue = 0

	waypointTravelSpeed = 35 # out of 100
	waypointThresh = 75 # millimeters
	waypoints = []
        mx = 0
        my = 0
        mz = 0
        mheading = 0

	def __init__(self, motorDriver):
		super(MotorController, self).__init__()
		self.driver = motorDriver()
		self.driver.setDC([0,0],[0,0])

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
		self.mPowers = [0, 0]
		self.driver.setDC(self.mPowers, self.direction)
		go = False

	def steeringThrottle(self, data):
		steering = util.transform(data[1], self.motorLowValue, self.motorHighValue, -1, 1)
		throttle = util.transform(data[2], self.motorLowValue, self.motorHighValue, -1, 1)
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
		end = self.motorOffValue
		if throttle < 0:
			if steering < 0:
				# right motor should slow down, left motor should speed up
				L += sp
				R -= sm
			else:
				# left motor should slow down, right motor should speed up
				L -= sm
				R += sp
			end = self.motorHighValue
		else:
			if steering < 0:
				# left motor should slow down, right motor should speed up
				L -= sm
				R += sp
			else:
				# right motor should slow down, left motor should speed up
				L += sp
				R -= sm
			end = self.motorLowValue
		mL = util.transform(util.clampToRange(L, 0, 255), 0, 255, self.motorOffValue, end)
		mR = util.transform(util.clampToRange(R, 0, 255), 0, 255, self.motorOffValue, end)
                #sys.stdout.write(str(mL) + " " + str(mR) + "\n")
		self.changeMotorVals(mL, mR)

	# this function will consume the controllerQueue, which was filled by DDMCServer
	# and will change the motors powers and directions according to what was in the queue
	# it also will monitor that the bot is still receiving commands, and if it isn't, it will stop the bot
	def handleControllerQueue(self):
		#print self.state
		# if there hasn't been anything in the queue in half a second
		if self.state != self.VELOCITY_HEADING and time.time()-self.lastQueue > .5 and util.controllerQueue.empty():
			# stop the bot
			self.direction = [0, 0]
			self.mPowers = [0, 0]
			self.lastQueue = time.time()
		else:
			while not util.controllerQueue.empty(): # this is a while so that the most recent thing in the queue is the resultant command that is done
				good = True
				try:
					# nowait because this process was called from the main loop which controls the self.motors
					# so we don't want this function to block.
					data = util.controllerQueue.get_nowait()
				except Queue.Empty as msg: 
					# realistically this should never happen because we check to see that the queue is not empty
					# but it is shared memory, and who knows?
					good = False
				if good:
					mL = self.motorOffValue
					mR = self.motorOffValue
					if data[0] == self.STEERING_THROTTLE_OFFBOARD or data[0] == self.TANK: # recieved motor level commands
						self.state = data[0]
						mL = data[1]
						mR = data[2]
						self.changeMotorVals(mL, mR)
					elif data[0] == self.STEERING_THROTTLE_ONBOARD: # recieved joystick information (throttle, steering)
						#print data
						self.state = data[0]
						self.steeringThrottle(data)# this calls changeMotorVals()
					elif data[0] == self.VELOCITY_HEADING:
						print "velHeading entered"
						self.state = data[0]
						self.vhState = self.TURNING
						self.desiredVel = util.transform(data[1], self.motorLowValue, self.motorHighValue, -util.maxVel, util.maxVel)
						if abs(self.desiredVel) >= .1:
							self.mPowers = [0, 0]
							self.driver.setDC(self.mPowers, self.direction)
						self.desiredHeading = data[2]
						self.goToHeading(self.desiredHeading)
					elif data[0] == self.WAYPOINT:
						self.state = data[0]
						self.waypoints.append((data[1], data[2]))
						self.waypointNavigation()
					if self.state != self.WAYPOINT:
						# consume the queue so that way when the robot is switched to waypoint, it gets fresh data
						while not util.positionQueue.empty():
							util.positionQueue.get_nowait()
						self.waypoints = []
					self.lastQueue = time.time()

	# this sets up the values used to drive the motors 
	# it does not drive the motor because this function is tied to the queue
	# and only gets executed when something is in the queue
	# yet we want the motors to be constantly receiving contol information
	# motorLowValue <= mL,mR <= motorHighValue, motorOffValue means the wheels wont turn
	def changeMotorVals(self, mL, mR):
		if mL > self.motorOffValue:
			self.direction[self.LEFT] = 1
			self.mPowers[self.LEFT] = util.clampToRange(util.transform(mL, self.motorOffValue, self.motorHighValue, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		else:
			self.direction[self.LEFT] = 0
			self.mPowers[self.LEFT] = util.clampToRange(util.transform(mL, self.motorOffValue, self.motorLowValue, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		if self.mPowers[self.LEFT] < self.driver.minDC:
			self.mPowers[self.LEFT] = 0

		if mR > self.motorOffValue:
			self.direction[self.RIGHT] = 1
			self.mPowers[self.RIGHT] = util.clampToRange(util.transform(mR, self.motorOffValue, self.motorHighValue, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		else :
			self.direction[self.RIGHT] = 0
			self.mPowers[self.RIGHT] = util.clampToRange(util.transform(mR, self.motorOffValue, self.motorLowValue, 0, 100), self.driver.minDC-1, self.driver.maxDC)
		if self.mPowers[self.RIGHT] < self.driver.minDC:
			self.mPowers[self.RIGHT] = 0
		#print self.mPowers

		if self.state != self.VELOCITY_HEADING:
                        print self.mPowers
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
			sys.stdout.write("\n")
			dist = h*util.botWidth/2.0
			sys.stdout.write("dist=")
			print dist
			self.requiredCounts = int(abs(dist/util.distPerBlip))
			sys.stdout.write(" requiredCounts ")
			print self.requiredCounts
			self.mPowers = [50, 50]
			self.driver.setDC(self.mPowers,self.direction)

	def resetEncoders(self):
		self.gpioQueue.put(['resetEncoders'])

	# PID part of the wheel controller loop
	def controlPowers(self, vel, pin):	#TODO possible use mm/sec instead of m/s because it will be more accurate because floating point is bad
		if vel != -1:
			if self.desiredVel != 0:
				p = self.desiredVel-vel
				sys.stdout.write("Vel difference: ")
				sys.stdout.write(str(p))
				pPWM = 0
				if abs(p) >= util.minVel:
					if p > 0:
						pPWM = util.transform(p, util.minVel, util.maxVel, self.driver.minDC, self.driver.maxDC)
					else:
						pPWM = -util.transform(-p, util.minVel, util.maxVel, self.driver.minDC, self.driver.maxDC)
				sys.stdout.write("PWM effort: ")
				print pPWM
				if(pin == util.leftEncPin):
					self.mPowers[self.LEFT] = util.clampToRange(self.mPowers[self.LEFT]+pPWM, 0, 100)
				elif(pin == util.rightEncPin):
					self.mPowers[self.RIGHT] = util.clampToRange(self.mPowers[self.RIGHT]+pPWM, 0, 100)
				else:
					print "Encoder is reading data to an unexpected pin"
			else:
				self.mPowers = [0, 0]
			self.driver.setDC(self.mPowers, self.direction)

	def handleEncoderQueue(self):	
		while not util.encQueue.empty():	
			good = True
			try: 
				# nowait because this process was called from the main loop which controls the motors
				# so we don't want this function to block.
				data = util.encQueue.get_nowait()
			except Queue.Empty as msg:
				# realistically this should never happen because we check to see that the queue is not empty
				# but it is shared memory, and who knows?
				good = False
			if good: 
				if self.state == self.VELOCITY_HEADING:
					if self.vhState == self.TURNING:
						# note, does not check which motor moved the desired amount, possible change this
						print data
						if data[1] >= self.requiredCounts:
							self.vhState = self.DRIVING
							self.currentHeading = self.desiredHeading
							self.setDCByVel(self.desiredVel)
					else:
						# data[2] = seconds/blip
						# convert to rotations per second 
						# then multiply by distance wheel travels in one rotation
						# result is mm/second
						vel = -1
						if data[2] > -1:
							vel = util.stateChangesPerRevolution/data[2]
						sys.stdout.write("vel=")
						print vel
						sys.stdout.write("desiredVel=")
						print self.desiredVel
						# calls setDC()
						# pid part of the loop
						self.controlPowers(vel, data[0])
				elif self.state == self.ENCODER_TEST:
					print data
					if data[0] >= self.requiredCounts:
						print "wtf"
						self.mPowers = [0, 0]
						self.driver.setDC(self.mPowers, self.direction)
						time.sleep(1)
						self.mPowers = [35, 35]
						self.requiredCounts = util.stateChangesPerRevolution
						self.driver.setDC(self.mPowers, self.direction)

	def waypointNavigation(self):
		# consume queue until we get newest data
                do = False
		while not util.positionQueue.empty():
		    pos, self.mheading= util.positionQueue.get_nowait()
                    self.mx, self.my, self.mz = pos.split(", ")            
                    do = True
                if not do:
                    return
		x = self.waypoints[0][0]-int(self.mx)
		y = self.waypoints[0][1]-int(self.my)
		if math.fabs(x) > self.waypointThresh or math.fabs(y) > self.waypointThresh:
			#distance to travel = math.sqrt(x*x+y*y)
			theta = math.atan2(y,x)
			phi = theta-float(self.mheading)
                        if phi > math.pi:
                            phi -= 2*math.pi
                        elif phi < -math.pi:
                            phi += 2*math.pi
                        if phi > 0.10 and phi < math.pi/2.0:
				rm = self.waypointTravelSpeed
				lm = self.waypointTravelSpeed*math.cos(phi)*.4
			elif phi < -0.10 and phi > -math.pi/2.0:
				rm = self.waypointTravelSpeed*math.cos(phi)*.4
				lm = self.waypointTravelSpeed
                        elif phi < 3.1 and phi > math.pi/2.0:
                                rm = self.waypointTravelSpeed*.65
                                lm = 0
                        elif phi > -3.1 and phi < -math.pi/2.0:
                                rm = 0
                                lm = self.waypointTravelSpeed*.65
			else:
				rm = self.waypointTravelSpeed
				lm = self.waypointTravelSpeed
			self.mPowers = [math.fabs(lm), math.fabs(rm)]
			self.direction = [0 if rm < 0 else 1, 0 if lm < 0 else 1]
		else:
			self.waypoints.pop(0)
			self.mPowers = [0, 0]
			self.direction = [0, 0]
                        print("Waypoint done")
		self.driver.setDC(self.mPowers, self.direction)

	def run(self):
		self.go = True
		try:
			while self.go:
			#	print self.mPowers
			#	print self.direction
				self.handleControllerQueue()
				self.handleEncoderQueue()
				if self.state == self.WAYPOINT and len(self.waypoints) > 0:
					self.waypointNavigation()
		except KeyboardInterrupt as msg:
			print "KeyboardInterrupt detected. MotorContoller is terminating"
			self.go = False	
		except Exception as msg:
			print "Motor controller"
			print msg
			self.mPowers = [0, 0]
			self.driver.setDC(self.mPowers, [0, 0])
		finally:
			self.exitGracefully()

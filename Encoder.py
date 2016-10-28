import time
from multiprocessing import Process
from multiprocessing import Pipe
from multiprocessing import Queue

import util

# the fastest I have seen it move is 0.511192102610497 m/s

class Encoder(Process):
	pin = None 
	#pin should be util.leftEncPin or util.rightEncPin set by constructor 
	count = 0
	# will only put things into the queue
	driverQueue = None
	gpioQueue = None
	# used to shut the process down
	pipe = None
	go = True
	pSize = 10
	periods = [-1.0]*pSize
	periodIndex = 0
	timeout = .1 # seconds

	def __init__(self, *args, **kwargs):
		super(Encoder, self).__init__()
		for key in kwargs:
			if key == 'queue':
				self.driverQueue = kwargs[key]
			elif key == 'pipe':
				self.pipe = kwargs[key]
			elif key == 'pin':
				self.pin = kwargs[key]
			elif key == 'gpioQueue':
				self.gpioQueue = kwargs[key]

    	def setupPin(self): 
		self.gpioQueue.put(['setup', self.pin, 'INPUT'])

	def consumePipe(self):
		while self.pipe.poll():
			data = self.pipe.recv()
			if 'reset' == data:
				self.count = 0
				self.resetPeriod()
			elif len(data) == 3:
				# data[1] = level of pin
				# data[2] = time since request
				self.waitForEdgeResponse(data[1], data[2])
				self.gpioQueue.put(['waitForEdge', util.getIdentifier(self), self.pin, self.timeout])

	# if level = None a stall occured
	def waitForEdgeResponse(self, level, elapsedTime):
		if level == None: #Stall occured
			#TODO handle stall
			self.count = 0
			self.resetPeriod()
		else:
			self.count += 1
			self.periods[self.periodIndex] = elapsedTime
	# increment self.periodIndex and keep it within range of self.pSize = len(self.periods)
			self.periodIndex = (self.periodIndex+1)%self.pSize;
		self.driverQueue.put([self.pin ,self.count, self.getAveragePeriodBetweenBlips()])

	def resetPeriod(self):
		self.periods = [-1]*self.pSize
		self.periodIndex = 0

	# returns seconds/blip
	def getAveragePeriodBetweenBlips(self):
		ave = 0.0
		i = 0
		for i in range(0, self.pSize):
			if self.periods[i] == -1: # invalid period, therefore return what is got
				break
			else:
				ave += self.periods[i]
		# return average of valid periods, i+1 because i will never equal self.pSize
		return ave/(i+1)

	# TODO wait for edge
	def run(self):
		try:
			self.go = True
			self.gpioQueue.put(['waitForEdge', util.getIdentifier(self), self.pin, self.timeout])
			while self.go:
				self.consumePipe()
		except KeyboardInterrupt as msg:
			print "KeyboardInterrupt detected. EncoderProcess is terminating"
			self.go = False
		finally:
			self.pipe.close()
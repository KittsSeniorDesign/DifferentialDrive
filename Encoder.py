import sys
import util

# the fastest I have seen it move is 0.511192102610497 m/s

class Encoder:
	count = 0
	pSize = 40
	periods = [-1.0]*pSize
	periodIndex = 0
	timeout = .1

	def __init__(self):
		pass

	def edgeDetected(self, args):
		sys.stdout.write("args=")
		print args
		self.count += 1
		print self.count
		self.periods[self.periodIndex] = elapsedTime
	# increment self.periodIndex and keep it within range of self.pSize = len(self.periods)
		self.periodIndex = (self.periodIndex+1)%self.pSize;

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
		if i < 10:
			return -1
		else:
			return ave/(i+1)

	# if level = None a stall occured
	def waitForEdgeResponse(self, level, elapsedTime):
		if elapsedTime >= self.timeout: #Stall occured
			#TODO handle stall
			print "OH NO! A STALL"
			self.count = 0
			self.resetPeriod()
		else:
			self.count += 1
			self.periods[self.periodIndex] = elapsedTime
	# increment self.periodIndex and keep it within range of self.pSize = len(self.periods)
			self.periodIndex = (self.periodIndex+1)%self.pSize;
		util.encQueue.put([self.pin ,self.count, self.getAveragePeriodBetweenBlips()])

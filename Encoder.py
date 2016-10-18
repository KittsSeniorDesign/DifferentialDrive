import time
from multiprocessing import Process
from multiprocessing import Pipe
from multiprocessing import Queue

# the fastest I have seen it move is 0.511192102610497 m/s

class Encoder(Process):
	pin = None 
	#pin should be util.leftEncPin or util.rightEncPin set by constructor 
	count = 0
	# will only put things into the queue
	driverQueue = None
	# object used to interface with GPIO of the microcontroller
	driver = None
	# used to shut the process down
	pipe = None
	go = True
	pSize = 10
	periods = [-1.0]*pSize
	periodIndex = 0

	def __init__(self, *args, **kwargs):
		super(Encoder, self).__init__()
		for key in kwargs:
			if key == 'queue':
				self.driverQueue = kwargs[key]
			elif key == 'pipe':
				self.pipe = kwargs[key]
			elif key == 'pin':
				self.pin = kwargs[key]
                        elif key == 'driver':
				self.driver = kwargs[key]()

        def setupPin(self):
		self.driver.setupPin(self.pin)

	def checkIfShouldStop(self):
		if self.pipe.poll():
			data = self.pipe.recv()
			if 'stop' in data:
				self.go = False
				self.pipe.close()

	def resetPeriod(self):
		self.periods = [-1]*self.pSize
		self.periodIndex = 0

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

	def run(self):
		self.go = True
		while self.go:
			starttime = time.time()
			val = self.driver.waitForEdge()
			if val is None:		#Stall occured
				#TODO handle stall
				self.count = 0
				self.resetPeriod()
			else:
				self.count += 1
				self.periods[self.periodIndex] = time.time()-starttime
		# increment self.periodIndex and keep it within range of self.pSize = len(self.periods)
				self.periodIndex = (self.periodIndex+1)%self.pSize;
			self.driverQueue.put([self.pin ,self.count, self.getAveragePeriodBetweenBlips()])
			self.checkIfShouldStop()
		self.driver.exitGracefully()

if __name__ == '__main__':
	driver_queue = Queue()
	control_pipe, enc_pipe = Pipe()
	e = Encoder(queue=driver_queue, pipe=enc_pipe, pin=11)
	e.start()
	while True:
		while not driver_queue.empty():
			good = True
			try: 
				data = driver_queue.get()
			except Queue.Empty as msg:
				# realistically this should never happen because we check to see that the queue is not empty
				# but it is shared memory, and who knows?
				good = False
			if good:
				print data

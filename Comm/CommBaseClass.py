#!/usr/bin/env python

from multiprocessing import Process
from multiprocessing import Queue
# import signal so that main threads try except statement will catch keyboard interrupt
import thread, signal, struct, time, sys, os
sys.path.append(os.path.abspath('..'))
import util

class CommBaseClass(Process):
	# This queue is filled with the data that is sent from ground control to the robot
	# it is consumed by the pilot (whenever that gets written)
	recvQueue = None
	# This is the queue that gets filled by the position process.
	# it is consumed in this process and the data is sent to what is sending commands
	# to the robot
	sendQueue = None
	# This is to terminate the threads that are started
	go = True
	# This is to know how many bytes to read in recv(). recv() is implemented in child class
	# can also be set in handleIncomingData()
	#bytesToRead = 12
	bytesToRead = 6

	def __init__(self):
		super(CommBaseClass, self).__init__()
		self.recvQueue = util.controllerQueue
		self.sendQueue = util.positionTelemQueue

	def waitForConnection(self):
		raise NotImplementedError("Override waitForConnection in class that inherits CommBaseClass")

	# override this function in inherited class, but make sure to call this function in
	# the beginning. For example:
	# 	def resetClient(self, waitForReconnect = True):
	#		super(ChildClass, self).resetClient(waitForReconnect)
	# 		somecodes()
	def resetClient(self):
		print "Controller disconnected!"
		# Stop the bot
		self.recvQueue.put([3,1500,1500])
		# remember to inherit, override, and call super class function!!!

	# should be blocking
	# returns a list of the bytes recieved from a connection in the child class
	def recv(self):
		raise NotImplementedError("Override recv in class that inherits CommBaseClass")

	# don't override this unless necessary
	# This is called from run()
	def handleIncomingData(self):
		self.waitForConnection()
		while self.go:
			data = self.recv()
	                if len(data) == 0:
				self.resetClient()
				self.waitForConnection()
			elif len(data) == self.bytesToRead: # fill recvQueue for pilot to consume
				srcdstids = struct.unpack('<B', data[0])[0]
				controlScheme = struct.unpack('<B', data[1])[0]
				if controlScheme != 5: # defined as VELOCITY_HEADING in MotorController.py
                                        lm = struct.unpack('<h', data[2:4])[0] # left motor, steering, or velocity
			    	        rm = struct.unpack('<h', data[4:])[0] # right motor, throttle, or heading
					self.recvQueue.put([
						controlScheme, # control scheme
                                                lm, 
                                                rm])
				elif controlScheme == 5:
                                        wx = struct.unpack('>h', data[2:4])[0]
                                        print wx
                                        wy = struct.unpack('>h', data[4:])[0]
                                        self.recvQueue.put([
                                                controlScheme,
                                                wx,
                                                wy])
                                elif False:
					vel = struct.unpack('i', data[4:8])[0]
					heading = struct.unpack('<f', data[8:12])[0]
					self.recvQueue.put([
						controlScheme,
						vel,
						heading])

	# sends data across the connecion in the child class
	def send(self, data):
		raise NotImplementedError("Override send in class that inherits CommBaseClass")

	def handleOutgoingData(self):
		while not self.sendQueue.empty():
			d = self.sendQueue.get_nowait()	
			a = ''
			for i, p in enumerate(d) :
				if p is not None:
					a += p
					if i != len(d)-1: 
						a += ", "
			a += ";"
			self.send(a)

	def exitGracefully(self):
		raise NotImplementedError("Override exitGracefully in class that inherits CommBaseClass")

	def run(self):
		try:
			t = thread.start_new_thread(self.handleIncomingData, ())
			while self.go:
				self.handleOutgoingData() 
				time.sleep(.01)
		except KeyboardInterrupt as msg:
			print "KeyboardInterrupt detected. CommProcess is terminating"
			self.go = False
		finally:
			self.exitGracefully()

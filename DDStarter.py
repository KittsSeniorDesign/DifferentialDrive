#!/usr/bin/env python 

# This file was created by Ryan Cooper in 2016
# to control a raspberry pi that is hooked up to motor controls
# that control motors that create a differential drive
# it can be controlled by keyboard or by an controlServer controller (possibly any HCI controller)
import RPi.GPIO as GPIO
import time
import thread
import signal
import sys
from multiprocessing import Pipe
from multiprocessing import Queue
from multiprocessing import Manager

from MotorController import MotorController
from Encoder import Encoder

import util

class DDStarter:
	# encQueue in makeClasses() is filled by both Lencoder and Rencoder, and is consumed by motorController
	#	the array in encQueue is of the form [pin, count, timeSinceLast]
	# controllerQueue in makeClasses is filled by DDMCServer, and is consumed by motorController
	#	commands in the queue come from a DDMCClient
	# a manager creates Queues that are safe to share between processes
	motorController = None
	# Differential Drive Motor Controller (DDMC)
	controlServer = None
	Lencoder = None
	Rencoder = None
	# pipes are used to terminate processes
	ePipeLeft = None
	ePipeRight = None
	motorPipe = None
	controllerPipe = None
	
	def __init__(self):
		self.makeClasses()
		self.startProcesses()
		# Catch SIGINT from ctrl-c when run interactively.
		signal.signal(signal.SIGINT, self.signal_handler)
		# Catch SIGTERM from kill when running as a daemon.
		signal.signal(signal.SIGTERM, self.signal_handler)
		# This thread of execution will sit here until a signal is caught
		signal.pause()

	def makeClasses(self):
		# used to create multi-process safe queues
		manager = Manager()
		# pipes for process termination
		self.ePipeLeft, eLeft = Pipe() 
		self.ePipeRight, eRight = Pipe()
		self.motorPipe, m = Pipe() 
		self.controllerPipe , c = Pipe()
		# queues for interprocess communication
		encQueue = manager.Queue()
		controllerQueue = manager.Queue()
		(driver, commDriver) = self.determineDrivers()
		# passing arguments to processes
		self.motorController = MotorController(encQueue=encQueue, controllerQueue=controllerQueue, pipe=m, driver=driver)
		self.controlServer = commDriver(queue=controllerQueue, pipe=c)
		self.Lencoder = Encoder(queue=encQueue, pin=util.leftEncPin, pipe=eLeft)
		self.Rencoder = Encoder(queue=encQueue, pin=util.rightEncPin, pipe=eRight)

	def startProcesses(self):
		self.Lencoder.start()
		self.Rencoder.start()
		self.motorController.start()
		self.controlServer.start()

	def signal_handler(self, signal, frame):
		self.exitGracefully()

	def determineDrivers(self):
		sys.path.append('drivers/')
		# used to pull configuration from file
		microcontroller = ""
		driver = ""
		commDriver = ""
		conf = open('config.txt', 'r')
		line = conf.readline()
		while line != "":
			# if the first character is '#', this line is a comment
			if line[0] != '#':
				words = line.split()
				if len(words) > 0:
					# in all cases words[1] == '='
					if words[0] == 'microcontroller':
						microcontroller = words[2]
					elif words[0] == 'driver':
						driver = words[2]
					elif words[0] == 'commDriver':
						commDriver = words[2]
			line = conf.readline()
		conf.close()
		d = None
		comm = None
		if microcontroller == 'RPi':
			if driver == 'L298':
				try:
					import RPiL298Driver
				except ImportError as err:
					print "Could not import drivers/RPiL298Driver"
					sys.exit(1)
				else:
					d = RPiL298Driver.RPiL298Driver
		elif microcontroller == 'Edison':
			if driver == 'L298':
				try:
					import EdisonL298Driver
				except ImportError as err:
					print "Could not import drivers/EdisonL298Driver"
					sys.exit(1)
				else:
					d = EdisonL298Driver.EdisonL298Driver
					
		if commDriver == 'Wifi':
			try:
				import WifiServer
			except ImportError as err:
				print "Could not import drivers/WifiServer"
				sys.exit(1)
			else:
				comm = WifiServer.WifiServer
		#elif commDriver == 'Xbee':
		return (d, comm)

	def exitGracefully(self):
		try:
			print "Program was asked to terminate."
			if self.motorController:
				self.motorPipe.send('stop')	
			if self.controlServer:
				self.controllerPipe.send('stop')
			if self.Lencoder:
				self.ePipeLeft.send('stop')
			if self.Rencoder:
				self.ePipeRight.send('stop')
			sys.stdout.write("Waiting for threads to exit...")
			sys.stdout.flush()
			self.motorController.join()
			self.controlServer.join()
			self.Lencoder.join()
			self.Rencoder.join()
			print "Done"
			sys.exit(0)
		except Exception as msg:
			print "An exception occured while trying to terminate"
			print msg
			sys.exit(1)

if '__main__' ==  __name__:
	r = DDStarter()

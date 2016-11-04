#!/usr/bin/env python 

# This file was created by Ryan Cooper in 2016
# to control a raspberry pi that is hooked up to motor controls
# that control motors that create a differential drive
# it can be controlled by keyboard or by an commProcess controller (possibly any HCI controller)
from multiprocessing import Pipe
from multiprocessing import Queue
from multiprocessing import Manager
import time, sys, argparse, signal

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
	commProcess = None
	gpioProcess = None
	Lencoder = None
	Rencoder = None
	# pipes are used to terminate processes
	ePipeLeft = None
	ePipeRight = None
	# var that holds microcontroller info from config.txt
	microcontroller = ""
	
	def __init__(self):
		parser = argparse.ArgumentParser(description="Arguments are for debuggin only.")
		parser.add_argument('--encoders', dest='testEncoder', action="store_true", help="Starts encoder system test")
		args = parser.parse_args()
		if args.testEncoder:
			self.runEncoderTest()
		else:
			self.runNormally()
		# Catch SIGINT from ctrl-c when run interactively.
		signal.signal(signal.SIGINT, self.signal_handler)
		# Catch SIGTERM from kill when running as a daemon.
		signal.signal(signal.SIGTERM, self.signal_handler)
		# This thread of execution will sit here until a signal is caught
		signal.pause()

	def signal_handler(self, signal, frame):
		self.exitGracefully()

	# TODO
	def runEncoderTest(self):
		# used to create multi-process safe queues
		manager = Manager()
		# pipes for process termination
		self.ePipeLeft, eLeft = Pipe() 
		self.ePipeRight, eRight = Pipe()
		# queues for interprocess communication
		encQueue = manager.Queue()
		controllerQueue = manager.Queue()
		gpioQueue = manager.Queue()
		# Only consumed at this time
		# consumtion is by commProcess
		# TODO make a process fill gcsDataQueue
		gcsDataQueue = manager.Queue()
		(motorDriver, commDriver, encoderDriver, gpioDriver) = self.determineDrivers()
		# passing arguments to processes
		self.Lencoder = Encoder(queue=encQueue, pin=util.leftEncPin, pipe=eLeft, gpioQueue=gpioQueue)
		self.Rencoder = Encoder(queue=encQueue, pin=util.rightEncPin, pipe=eRight, gpioQueue=gpioQueue)
		self.gpioProcess = gpioDriver(gpioQueue, {util.getIdentifier(self.Lencoder): self.ePipeLeft, util.getIdentifier(self.Rencoder): self.ePipeRight})
		self.motorController = MotorController(encQueue=encQueue, encPipes=(self.ePipeLeft, self.ePipeRight), controllerQueue=controllerQueue, motorDriver=motorDriver, gpioQueue=gpioQueue)
		self.motorController.state = self.motorController.ENCODER_TEST
		self.motorController.requiredCounts = 40
		# have to setup pins afterward because gpioProcess needs to be setup first
		self.Lencoder.setupPin()
		self.Rencoder.setupPin()
		self.gpioProcess.start()
		self.Lencoder.start()
		self.Rencoder.start()
		self.motorController.start()
		self.motorController.driver.setDC([100,100], [0,0])


	def runNormally(self):
		# used to create multi-process safe queues
		manager = Manager()
		# pipes for process termination
		self.ePipeLeft, eLeft = Pipe() 
		self.ePipeRight, eRight = Pipe()
		# queues for interprocess communication
		encQueue = manager.Queue()
		controllerQueue = manager.Queue()
		gpioQueue = manager.Queue()
		# Only consumed at this time
		# consumtion is by commProcess
		# TODO make a process fill gcsDataQueue
		gcsDataQueue = manager.Queue()
		(motorDriver, commDriver, encoderDriver, gpioDriver) = self.determineDrivers()
		# passing arguments to processes
		self.Lencoder = Encoder(queue=encQueue, pin=util.leftEncPin, pipe=eLeft, gpioQueue=gpioQueue)
		self.Rencoder = Encoder(queue=encQueue, pin=util.rightEncPin, pipe=eRight, gpioQueue=gpioQueue)
		self.gpioProcess = gpioDriver(gpioQueue, {util.getIdentifier(self.Lencoder): self.ePipeLeft, util.getIdentifier(self.Rencoder): self.ePipeRight})
		self.motorController = MotorController(encQueue=encQueue, encPipes=(self.ePipeLeft, self.ePipeRight), controllerQueue=controllerQueue, motorDriver=motorDriver, gpioQueue=gpioQueue)
		self.commProcess = commDriver(recvQueue=controllerQueue, sendQueue=gcsDataQueue)
		# have to setup pins afterward because gpioProcess needs to be setup first
		self.Lencoder.setupPin()
		self.Rencoder.setupPin()
		self.gpioProcess.start()
		self.Lencoder.start()
		self.Rencoder.start()
		self.motorController.start()
		self.commProcess.start()

	def determineDrivers(self):
		sys.path.append('drivers/')
		sys.path.append('GPIO/')
		sys.path.append('Comm/')
		# used to pull configuration from file
		util.microcontroller = ""
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
						util.microcontroller = words[2]
					elif words[0] == 'driver':
						driver = words[2]
					elif words[0] == 'commDriver':
						commDriver = words[2]
			line = conf.readline()
		conf.close()

		motorDriver = None
		comm = None
		enc = None
		gpio = None

		if util.microcontroller == 'RPi':
			try:
				import RPiGPIODriver
			except ImportError as err:
				print err
				print "Could not import RPiGPIODriver"
				sys.exit(1)
			else:
				gpio = RPiGPIODriver.RPiGPIODriver
		elif util.microcontroller == 'Edison':
			try:
				import EdisonGPIODriver
			except ImportError as err:
				print err
				print "Could not import EdisonGPIODriver"
				sys.exit(1)
			else:
				gpio = EdisonGPIODriver.EdisonGPIODriver

		if driver == 'L298':
			try:
				import L298Driver
			except ImportError as err:
				print "Could not import L298Driver"
				sys.exit(1)
			else:
				motorDriver = L298Driver.L298Driver
		if commDriver == 'Wifi':
			try:
				import WifiComm
			except ImportError as err:
				print "Could not import Comm/WifiComm"
				sys.exit(1)
			else:
				comm = WifiComm.WifiComm
		elif commDriver == 'Xbee':
			try:
				import XbeeComm
			except ImportError as err:
				print "Could not import Comm/XbeeComm"
				sys.exit(1)
		return (motorDriver, comm, enc, gpio)

	def exitGracefully(self):
		try:
			print "Program was asked to terminate."
			print "Waiting for processes to exit..."
			self.commProcess.join()
			self.gpioProcess.join()
			self.motorController.join()
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

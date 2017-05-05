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
	positionerProcess = None
	# pipes are used to terminate processes
	ePipeLeft = None
	ePipeRight = None
	# var that holds microcontroller info from config.txt
	microcontroller = ""
	
	def __init__(self):
		parser = argparse.ArgumentParser(description="Arguments are for debuggin only.")
		parser.add_argument('--encoders', dest='testEncoder', action="store_true", help="Starts encoder system test")
		args = parser.parse_args()
		self.setupIPC()
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

	def setupIPC(self):
		# used to create multi-process safe queues
		manager = Manager()
		# queues for interprocess communication
		util.encQueue = manager.Queue()
		util.controllerQueue = manager.Queue()
		util.gpioQueue = manager.Queue()
		util.positionQueue = manager.Queue()
		util.positionTelemQueue = manager.Queue()

	# TODO
	def runEncoderTest(self):
		(motorDriver, commDriver, encoderDriver, gpioDriver) = self.determineDrivers()
		# passing arguments to processes
		self.gpioProcess = gpioDriver([util.leftEncPin, util.rightEncPin])
		self.motorController = MotorController(motorDriver)
		self.motorController.state = self.motorController.ENCODER_TEST
		self.motorController.requiredCounts = 20
		# have to setup pins afterward because gpioProcess needs to be setup first
		self.gpioProcess.start()
		self.motorController.start()
		self.motorController.driver.setDC([30,30], [0,0])


	def runNormally(self):
		(motorDriver, commDriver, encoderDriver, gpioDriver, positioner) = self.determineDrivers()
		# passing arguments to processes
		self.gpioProcess = gpioDriver([util.leftEncPin, util.rightEncPin])
		self.motorController = MotorController(motorDriver)
		self.commProcess = commDriver()
		self.positionerProcess = positioner()
		# have to setup pins afterward because gpioProcess needs to be setup first
		self.gpioProcess.start()
		self.motorController.start()
		self.commProcess.start()
		self.positionerProcess.start()

	def determineDrivers(self):
		sys.path.append('drivers/')
		sys.path.append('GPIO/')
		sys.path.append('Comm/')
		sys.path.append('Positioner/')
		# used to pull configuration from file
		util.microcontroller = ""
		driver = ""
		commDriver = ""
		positionDriver = ""
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
					elif words[0] == 'positionDriver':
						positionDriver = words[2]
			line = conf.readline()
		conf.close()
		motorDriver = None
		comm = None
		enc = None
		gpio = None
		postioner = None

		if util.microcontroller == 'RPi':
			try:
				import RPiGPIODriver
			except ImportError as err:
				print err
				print "Could not import RPiGPIODriver"
				sys.exit(1)
			gpio = RPiGPIODriver.RPiGPIODriver
		elif util.microcontroller == 'Edison':
			try:
				import EdisonGPIODriver
			except ImportError as err:
				print err
				print "Could not import EdisonGPIODriver"
				sys.exit(1)
			gpio = EdisonGPIODriver.EdisonGPIODriver

		if driver == 'L298':
			try:
				import L298Driver
			except ImportError as err:
				print "Could not import L298Driver"
				sys.exit(1)
			motorDriver = L298Driver.L298Driver
		if commDriver == 'Wifi':
			try:
				import WifiComm
			except ImportError as err:
				print "Could not import Comm/WifiComm"
				sys.exit(1)
			comm = WifiComm.WifiComm
		elif commDriver == 'Xbee':
			try:
				import XbeeComm
			except ImportError as err:
				print "Could not import Comm/XbeeComm"
				sys.exit(1)
			comm = XbeeComm.XbeeComm
		elif commDriver == 'UnixSocket':
			try:
				import UnixSocketComm
			except ImportError as err:
				print "Could not import Comm/UnixSocketComm"
				sys.exit(1)
			comm = UnixSocketComm.UnixSocketComm
		if positionDriver == 'Pozyx':
			try:
				import PozyxPositioner
			except ImportError as err:
				print err
				print "Could not import Positioner/Pozyx"
				sys.exit(1)
			positioner = PozyxPositioner.PozyxPositioner
		return (motorDriver, comm, enc, gpio, positioner)

	def exitGracefully(self):
		try:
			print "Program was asked to terminate."
			print "Waiting for processes to exit..."
			if self.commProcess:
				self.commProcess.join()
			if self.motorController:
				self.motorController.join()
			if self.gpioProcess:
				self.gpioProcess.join()
			if self.positionerProcess:
				self.positionerProcess.join()
			print "Done"
			sys.exit(0)
		except Exception as msg:
			print "An exception occured while trying to terminate"
			print msg
			sys.exit(1)

if '__main__' ==  __name__:
	r = DDStarter()

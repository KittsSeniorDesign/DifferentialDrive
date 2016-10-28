#!/usr/bin/env python

# to install xbee:
# wget https://pypi.python.org/packages/53/13/c3f53a63b5a9d8890e7911580c466b25a90b732a500d437a1205fef47a68/XBee-2.2.3.tar.gz
# tar -xvf Xbee-2.2.3.tar
# cd Xbee-2.2.3
# python setup.py install
from xbee import XBee
# install with:
# pip install pyserial
import serial
import time

from CommBaseClass import CommBaseClass
import threading

class XbeeComm(CommBaseClass):

	ser = None
	xbee = None
	# variable used to make sure there is no race condition on recvData
	dataCondition = None
	recvData = None
	
	def __init__(self, recvQueue, sendQueue):
		super(XbeeComm, self).__init__(recvQueue, sendQueue)
		self.ser = serial.Serial('/dev/ttyAMA0', 9600)
		self.xbee = XBee(self.ser, callback=self.fillRecv)
		dataCondition = threading.Condition()

	def waitForConnection(self):
		pass

	def resetClient(self):
		pass

	def fillRecv(self, data):
		dataCondition.acquire()
		recvData = data
		dataConditon.release()
		dataCondition.notifyAll()

	def recv(self):
		# possible use this function for synchronous mode. Will it work in threads?
		# return self.xbee.wait_read_frame()

		# wait until self.fillRecv(data) fills recvData 
		dataCondition.wait()
		dataCondition.acquire()
		d = recvData
		recvData = None
		dataCondition.release()
		return d


	def send(self, data):
		self.xbee.send('at' param=data)

	def exitGracefully(self):
		self.xbee.halt()
		self.ser.close()
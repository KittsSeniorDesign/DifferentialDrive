#!/usr/bin/env python

#DDMC=Differential Drive Motor Control

# This file was created by Ryan Cooper in 2016
# This class starts a server to listen to an xbox controller which is plugged into a 
# client computer that can connect to the robot
import socket, time, sys

from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Pipe

from CommBaseClass import CommBaseClass

class UnixSocketComm(CommBaseClass):
	sock = None 
	connected = False

	def __init__(self):
		super(UnixSocketComm, self).__init__()
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		#self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # TODO figure out if this is necessary
		# listen for only one connection

	def waitForConnection(self):
		while not self.connected:
			try:
				self.sock.connect('uds_socket')
				self.connected = True
			except socket.error, msg:
				print "couldn't connect to unix domain socket. Is the java server running?"
				print >>sys.stderr, msg
                                time.sleep(1)

	def resetClient(self):
		super(UnixSocketComm, self).resetClient()
		self.sock.close()
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

	def recv(self):
		if self.connected:
                        return self.sock.recv(self.bytesToRead)
		else:
			return 0	

	def handleIncomingData(self):
		try:
			super(UnixSocketComm, self).handleIncomingData()
		except socket.error as msg:
			self.resetClient()
			self.waitForConnection()

	def send(self, data):
		if self.connected:
			self.sock.sendall(data)
			
	def exitGracefully(self):
		if self.sock:
			self.sock.close()


#DDMC=Differential Drive Motor Control

# This file was created by Ryan Cooper in 2016
# This class starts a server to listen to an xbox controller which is plugged into a 
# client computer that can connect to the robot
import socket, time, sys
from socket import error as socket_error

from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Pipe

from CommBaseClass import CommBaseClass

class WifiComm(CommBaseClass):
	serversocket = None 
	clientsocket = None

	def __init__(self, recvQueue, sendQueue):
		super(WifiComm, self).__init__(recvQueue, sendQueue)
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.serversocket.bind(('', 12345))
		# listen for only one connection
		self.serversocket.listen(1)
		print "Wifi server started"

	def waitForConnection(self):
		if self.clientsocket == None:
			connected = False
			while not connected:
				try:
					sys.stdout.write('Waiting for DDMCClient connection... ')
					sys.stdout.flush()
					(self.clientsocket, address) = self.serversocket.accept()
					connected = True
					print 'DDMC controller connected'
				except Exception as msg:
					print 'Client connection failed with message:'
					print msg
					print 'I will retry connecting in one second.'
					time.sleep(1)

	def resetClient(self):
		super(WifiComm, self).resetClient()
		if self.clientsocket:
			self.clientsocket.close()
		self.clientsocket = None

	def recv(self):
		if self.clientsocket:
			return self.clientsocket.recv(self.bytesToRead)
		else:
			return 0	

	def handleIncomingData(self):
		try:
			super(WifiComm, self).handleIncomingData()
		except socket_error as msg:
			self.resetClient()
			self.waitForConnection()

	def send(self, data):
		self.clientsocket.send(data)
			
	def exitGracefully(self):
		if self.clientsocket:
			self.clientsocket.close()
		if self.serversocket:
			self.serversocket.close()

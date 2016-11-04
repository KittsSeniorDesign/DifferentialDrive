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

from CommBaseClass import CommBaseClass
import threading

class XbeeComm(CommBaseClass):

	ser = None
	xbee = None
	# variable used to make sure there is no race condition on recvData
	dataCondition = None
	recvData = None
	# Hopefully this is the coordinator
	dest_addr = 0
	
	def __init__(self, recvQueue, sendQueue):
		super(XbeeComm, self).__init__(recvQueue, sendQueue)
		self.ser = serial.Serial('/dev/ttyAMA0', 9600)
		self.dataCondition = threading.Condition()
		self.xbee = XBee(self.ser, callback=self.fillRecv)

	def waitForConnection(self):
		pass

	def resetClient(self):
		pass

	# I decided to make use of an asychronous callback to recieve data instead
	# of the xbee.wait_read_frame() because I wanted this process's thread to wait
	# not the Xbees thread to wait
	def fillRecv(self, data):
		self.dataCondition.acquire()
		self.recvData = data
		self.dataConditon.release()

	def recv(self):
		# possible use this function for synchronous mode. Will it work in threads?
		# return self.xbee.wait_read_frame()

		# wait until self.fillRecv(data) fills recvData 
		self.dataCondition.wait()
		self.dataCondition.acquire()
		d = self.recvData
		self.recvData = None
		self.dataCondition.release()
		return d

 ''' Put here for reference, taken from python module xbee.ieee.Xbee 
 #Format: 
    #        {name of command:
    #           [{name:field name, len:field length, default: default value sent}
    #            ...
    #            ]
    #         ...
    #         }
    api_commands = {"at":
                        [{'name':'id',        'len':1,      'default':b'\x08'},
                         {'name':'frame_id',  'len':1,      'default':b'\x00'},
                         {'name':'command',   'len':2,      'default':None},
                         {'name':'parameter', 'len':None,   'default':None}],
                    "queued_at":
                        [{'name':'id',        'len':1,      'default':b'\x09'},
                         {'name':'frame_id',  'len':1,      'default':b'\x00'},
                         {'name':'command',   'len':2,      'default':None},
                         {'name':'parameter', 'len':None,   'default':None}],
                    "remote_at":
                        [{'name':'id',              'len':1,        'default':b'\x17'},
                         {'name':'frame_id',        'len':1,        'default':b'\x00'},
                         # dest_addr_long is 8 bytes (64 bits), so use an unsigned long long
                         {'name':'dest_addr_long',  'len':8,        'default':struct.pack('>Q', 0)},
                         {'name':'dest_addr',       'len':2,        'default':b'\xFF\xFE'},
                         {'name':'options',         'len':1,        'default':b'\x02'},
                         {'name':'command',         'len':2,        'default':None},
                         {'name':'parameter',       'len':None,     'default':None}],
                    "tx_long_addr":
                        [{'name':'id',              'len':1,        'default':b'\x00'},
                         {'name':'frame_id',        'len':1,        'default':b'\x00'},
                         {'name':'dest_addr',       'len':8,        'default':None},
                         {'name':'options',         'len':1,        'default':b'\x00'},
                         {'name':'data',            'len':None,     'default':None}],
                    "tx":
                        [{'name':'id',              'len':1,        'default':b'\x01'},
                         {'name':'frame_id',        'len':1,        'default':b'\x00'},
                         {'name':'dest_addr',       'len':2,        'default':None},
                         {'name':'options',         'len':1,        'default':b'\x00'},
                         {'name':'data',            'len':None,     'default':None}]
                    }
'''
	def send(self, d):
		self.xbee.send("tx", data=d, dest_addr=self.dest_addr)

	def exitGracefully(self):
		# need to halt to stop process that is listening for data
		self.xbee.halt()
		self.ser.close()

#!/usr/bin/env python

from multiprocessing import Process
from multiprocessing import Queue

import signal, time, sys, os
sys.path.append(os.path.abspath('..'))
import util

class PositionerBaseClass(Process):

	def __init__(self):
		super(PositionerBaseClass, self).__init__()

	def getPosition(self):
		raise NotImplementedError("Override getPosition in class that inherits PositionerBaseClass")	

	def sendError(self):
		raise NotImplementedError("Override sendError in class that inherits PositionerBaseClass")	

	def run(self):
        try:
            while self.go:
                pos = self.getPosition()
                if pos:
                	util.positionQueue.put(pos)
                else:
                	self.sendError()
                time.sleep(.01)
        except KeyboardInterrupt as msg:
            print "KeyboardInterrupt detected. CommProcess is terminating"
            self.go = False
        finally:
            self.exitGracefully()
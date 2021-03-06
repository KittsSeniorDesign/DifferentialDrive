#!/usr/bin/env python

from multiprocessing import Process
from multiprocessing import Queue

import signal, time, sys, os
sys.path.append(os.path.abspath('..'))
import util

class PositionerBaseClass(Process):

        timeBetweenPositionUpdates = .1

	def __init__(self):
		super(PositionerBaseClass, self).__init__()

	def getPosition(self):
		raise NotImplementedError("Override getPosition in class that inherits PositionerBaseClass")	

	def getHeading(self):
		raise NotImplementedError("Override getHeading in class that inherits PositionerBaseClass")

	def sendError(self):
		raise NotImplementedError("Override sendError in class that inherits PositionerBaseClass")	

	def run(self):
            try:
                while self.go:
                    pos = self.getPosition()
                    mag = self.getHeading()
                    if pos:
						util.positionQueue.put((pos, mag))
						util.positionTelemQueue.put((pos, mag))
                    else:
						print "pos undef"
                    time.sleep(self.timeBetweenPositionUpdates)
            except KeyboardInterrupt as msg:
                print "KeyboardInterrupt detected. CommProcess is terminating"
                self.go = False
            finally:
                self.exitGracefully()

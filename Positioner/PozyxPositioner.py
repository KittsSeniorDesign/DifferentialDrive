#!/usr/bin/env python
"""
Heavily based upon the Pozyx ready to localize tutorial (c) Pozyx Labs
Documentation on the code used here can be found at:
https://www.pozyx.io/Documentation/Tutorials/ready_to_localize/Python
"""
from time import sleep
import sys, os

from pypozyx import *
import __future__
from Positioner import PositionerBaseClass

sys.path.append(os.path.abspath('..'))
import util

import math

class PozyxPositioner(PositionerBaseClass):
    go = True
    aSize = 5
    ax = [0] * aSize
    ay = [0] * aSize
    flag = 0
    num = 0
    deltathres = 250
    thresmax = deltathres * 2
    px = 0
    py = 0
    def __init__(self):
        super(PozyxPositioner, self).__init__()
        # shortcut to not have to find out the port yourself
        serial_port = None
        try:
            print get_serial_ports()[0].device
            serial_port = get_serial_ports()[0].device
        except IndexError as msg:
            print("Could not find serial connection to pozyx. Positioner will be turned off for this run")
        if serial_port is not None:
            remote_id = 0x6048                 # remote device network ID
            remote = False                   # whether to use a remote device
            if not remote:
                remote_id = None

        # necessary data for calibration, change the IDs and coordinates yourself
            #anchors = [DeviceCoordinates(0x6019, 1, Coordinates(0, 0, 1482)),
            #           DeviceCoordinates(0x6049, 1, Coordinates(3921, 0, 1759)),
            #           DeviceCoordinates(0x6044, 1, Coordinates(0, 2579, 1670)),
            #           DeviceCoordinates(0x607F, 1, Coordinates(3946, 2854, 1575))]
            anchors = [DeviceCoordinates(0x6019, 1, Coordinates(0, 0, 73)),
                       DeviceCoordinates(0x6049, 1, Coordinates(3921, 0, 73)),
                       DeviceCoordinates(0x6044, 1, Coordinates(0, 2579, 73)),
                       DeviceCoordinates(0x607F, 1, Coordinates(3946, 2854, 73))]
            algorithm = POZYX_POS_ALG_UWB_ONLY  # positioning algorithm to use
            dimension = POZYX_2D    #POZYX_3D               # positioning dimension
            height = 0                      # height of device, required in 2.5D positioning
            pozyx = PozyxSerial(serial_port)
            self.initializePozyx(pozyx, anchors, algorithm, dimension, height, remote_id)
        else:
            self.go = False

    def initializePozyx(self, pozyx, anchors, algorithm=POZYX_POS_ALG_UWB_ONLY, dimension=POZYX_3D, height=1000, remote_id=None):
        self.pozyx = pozyx
        self.anchors = anchors
        self.algorithm = algorithm
        self.dimension = dimension
        self.height = height
        self.remote_id = remote_id
        self.pozyx.clearDevices(self.remote_id)
        self.setAnchorsManual()

    def getPosition(self):
        if not self.go:
            return "0, 0, 0"
        position = Coordinates()
        status = self.pozyx.doPositioning(position, self.dimension, self.height, self.algorithm, remote_id=self.remote_id)
        if status == POZYX_SUCCESS:
            return self.mMedian(position)
            #return self.filtering(position)
        else:
            return None

    def getHeading(self):
        if not self.go:
            return "0.0"
        orientation = EulerAngles()
    	status = self.pozyx.getEulerAngles_deg(orientation)
        heading = -math.radians(orientation.heading)
        heading = heading if heading >= -math.pi else heading+2*math.pi
        return str(heading)

    def publishPosition(self, position):
        network_id = self.remote_id
        if network_id is None:
            network_id = 0
        position.x = position.x / 25.4
        position.y = position.y / 25.4
        position.z = position.z / 25.4
        print "POS ID {}, x(mm): {pos.x} y(mm): {pos.y} z(mm): {pos.z}".format(
            "0x%0.4x" % network_id, pos=position)
        util.positionQueue.put(position)

    def sendError(self, operation):
        error_code = SingleRegister()
        network_id = self.remote_id
        if network_id is None:
            self.pozyx.getErrorCode(error_code)
            print "ERROR %s, local error code %s" % (operation, str(error_code))
            util.positionQueue.put(str(error_code));
            return
        status = self.pozyx.getErrorCode(error_code, self.remote_id)
        if status == POZYX_SUCCESS:
            print "ERROR %s on ID %s, error code %s" % (operation, "0x%0.4x" % network_id, str(error_code))
            util.positionQueue.put(str(error_code));
            return
        else:
            self.pozyx.getErrorCode(error_code)
            print "ERROR %s, couldn't retrieve remote error code, local error code %s" % (operation, str(error_code))
            util.positionQueue.put(str(error_code));
            return
            # should only happen when not being able to communicate with a remote Pozyx.

    def setAnchorsManual(self):
        """Adds the manually measured anchors to the Pozyx's device list one for one."""
        status = self.pozyx.clearDevices(self.remote_id)
        for anchor in self.anchors:
            status &= self.pozyx.addDevice(anchor, self.remote_id)
        if len(self.anchors) > 4:
            status &= self.pozyx.setSelectionOfAnchors(POZYX_ANCHOR_SEL_AUTO, len(self.anchors))
        return status

    def publishAnchorConfiguration(self):
        for anchor in self.anchors:
            print "ANCHOR,0x%0.4x,%s" % (anchor.network_id, str(anchor.coordinates))

    def exitGracefully(self):
        pass

    def mMedian(self, position):
        inum = self.num % self.aSize
        if self.num < self.aSize:
            self.ax[self.num] = position.x
            self.ay[self.num] = position.y
        else:
            self.ax[inum] = position.x
            self.ay[inum] = position.y
        self.ax.sort()
        self.ay.sort()
        self.px = self.ax[2]
        self.py = self.ay[2]
        self.num = self.num + 1
        return str(self.px) + ", " + str(self.py) + ", " + str(0)

    def filtering(self, position):
        inum = self.num % self.aSize
        if self.num < self.aSize:
            self.ax[self.num] = position.x
            self.ay[self.num] = position.y
            self.px = position.x
            self.py = position.y
        else:
            avgx = self.average(self.ax)
            avgy = self.average(self.ay)
            if abs(position.x-avgx) < self.deltathres and abs(position.y-avgy) < self.deltathres:
                self.ax[inum] = position.x
                self.ay[inum] = position.y
                self.px = position.x
                self.py = position.y
                self.flag = 0
            else:
                if self.flag > 8 and abs(position.x-avgx) < self.thresmax and abs(position.y-avgy) < self.thresmax:
                    self.ax[inum] = position.x
                    self.ax[inum] = position.y
                    self.px = position.x
                    self.py = position.y
                    self.flag = self.flag - 3
                else:
                    self.flag = self.flag + 1
        self.num = self.num + 1
        return  str(self.px) + ", " + str(self.py) + ", " + str(0)
        
    def average(self, s):
        return sum(s) * 1.0 / len(s)
    
    def variance(self, s):
        return map(lambda x: (x - self.average(s)) **2, s)
    
    def std_dev(self, s):
        return math.sqrt(self.average(self.variance(s)))

if __name__ == "__main__":
    p = PozyxPositioner()

    while True:
        pos = p.getPosition()
        px, py, pz = pos.split(', ', 2) 
        px = int(px)
        py = int(py)
        pz = int(pz)
        print(px, py, pz)
                
        sleep(.3)
    #while True:
    	#pos = p.getPosition()
        #head = p.getHeading()
    	#if pos:
        #	print(pos)
        #        print(head)
    	#sleep(.5)

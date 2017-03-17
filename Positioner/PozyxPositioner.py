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

class PozyxPositioner(PositionerBaseClass):
    go = True

    def __init__(self):
        super(PozyxPositioner, self).__init__()
        # shortcut to not have to find out the port yourself
        serial_port = None
        try:
            serial_port = get_serial_ports()[0].device
        except IndexError as msg:
            print("Could not find serial connection to pozyx. Positioner will be turned off for this run")
        if serial_port is not None:
            remote_id = 0x6069                 # remote device network ID
            remote = False                   # whether to use a remote device
            if not remote:
                remote_id = None

        # necessary data for calibration, change the IDs and coordinates yourself
            anchors = [DeviceCoordinates(0x6019, 1, Coordinates(0, 0, 196)),
                       DeviceCoordinates(0x6049, 1, Coordinates(3874, 0, 232)),
                       DeviceCoordinates(0x6044, 1, Coordinates(0, 2451, 174)),
                       DeviceCoordinates(0x607F, 1, Coordinates(3874, 2775, 155))]

            algorithm = POZYX_POS_ALG_UWB_ONLY  # positioning algorithm to use
            dimension = POZYX_3D    #POZYX_3D               # positioning dimension
            height = 1000                      # height of device, required in 2.5D positioning
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
        status = self.pozyx.doPositioning(position, self.dimension, 
self.height, self.algorithm, remote_id=self.remote_id)
        if status == POZYX_SUCCESS:
            return str(position.x) + ", " + str(position.y) + ", " + str(position.z)
        else:
            return None

    def getHeading(self):
        if not self.go:
            return "0.0"
        orientation = EulerAngles()
    	status = self.pozyx.getEulerAngles_deg(orientation)
        return str(orientation.heading)

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

if __name__ == "__main__":
    p = PozyxPositioner()
    while True:
    	pos = p.getPosition()
        head = p.getHeading()
	if pos:
        	print(pos)
                print(head)
    	sleep(.5)

#!/usr/bin/env python
"""
Heavily based upon the Pozyx ready to localize tutorial (c) Pozyx Labs
Documentation on the code used here can be found at:
https://www.pozyx.io/Documentation/Tutorials/ready_to_localize/Python
"""
from time import sleep

from pypozyx import *

sys.path.append(os.path.abspath('..'))
import util

class PozyxPositioner(PositionerBaseClass):
    go = True

    def __init__():
        super(PozyxPositioner, self).__init__()
        # shortcut to not have to find out the port yourself
        serial_port = get_serial_ports()[0].device

        remote_id = 0x6069                 # remote device network ID
        remote = False                   # whether to use a remote device
        if not remote:
            remote_id = None

        # necessary data for calibration, change the IDs and coordinates yourself
        anchors = [DeviceCoordinates(0x6019, 1, Coordinates(0, 0, 1460)),
                   DeviceCoordinates(0x6049, 1, Coordinates(3874, 0, 1460)),
                   DeviceCoordinates(0x6044, 1, Coordinates(0, 2451, 1460)),
                   DeviceCoordinates(0x6074, 1, Coordinates(3874, 2775, 2790))]

        algorithm = POZYX_POS_ALG_UWB_ONLY  # positioning algorithm to use
        dimension = POZYX_2_5D    #POZYX_3D               # positioning dimension
        height = 1000                      # height of device, required in 2.5D positioning
        pozyx = PozyxSerial(serial_port)
        self.initializePozyx(pozyx, anchors, algorithm, dimension, height, remote_id)

    def initialize(self, pozyx, anchors, algorithm=POZYX_POS_ALG_UWB_ONLY, dimension=POZYX_3D, height=1000, remote_id=None):
        self.pozyx = pozyx
        self.anchors = anchors
        self.algorithm = algorithm
        self.dimension = dimension
        self.height = height
        self.remote_id = remote_id
        self.pozyx.clearDevices(self.remote_id)
        self.setAnchorsManual()

    def getPosition(self):
        position = Coordinates()
        status = self.pozyx.doPositioning(position, self.dimension, self.height, self.algorithm, remote_id=self.remote_id)
        if status == POZYX_SUCCESS:
            return position
        else:
            return None

    def publishPosition(self, position):
        network_id = self.remote_id
        if network_id is None:
            network_id = 0
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
        if len(anchors) > 4:
            status &= self.pozyx.setSelectionOfAnchors(POZYX_ANCHOR_SEL_AUTO, len(anchors))
        return status

'''
   def printPublishConfigurationResult(self):
        """Prints and potentially publishes the anchor configuration result in a human-readable way."""
        list_size = SingleRegister()

        status = self.pozyx.getDeviceListSize(list_size, self.remote_id)
        print("List size: {0}".format(list_size[0]))
        if list_size[0] != len(self.anchors):
            self.printPublishErrorCode("configuration")
            return
        device_list = DeviceList(list_size=list_size[0])
        status = self.pozyx.getDeviceIds(device_list, self.remote_id)
        print("Calibration result:")
        print("Anchors found: {0}".format(list_size[0]))
        print("Anchor IDs: ", device_list)

        for i in range(list_size[0]):
            anchor_coordinates = Coordinates()
            status = self.pozyx.getDeviceCoordinates(
                device_list[i], anchor_coordinates, self.remote_id)
            print("ANCHOR,0x%0.4x, %s" % (device_list[i], str(anchor_coordinates)))
            if self.osc_udp_client is not None:
                self.osc_udp_client.send_message(
                    "/anchor", [device_list[i], int(anchor_coordinates.x), int(anchor_coordinates.y), int(anchor_coordinates.z)])
                sleep(0.025)
'''

    def publishAnchorConfiguration(self):
        for anchor in self.anchors:
            print "ANCHOR,0x%0.4x,%s" % (anchor.network_id, str(anchor.coordinates))

    def exitGracefully(self):
        pass

if __name__ == "__main__":
    p = PozyxPositioner()
    while True:
    	print(p.getPosition())
    	sleep(.5)
#!/bin/bash
#java -jar DataturbineExporter.jar 192.168.43.38:3333 uds_socket robot_1&
java -jar DataturbineExporter.jar 192.168.1.134:3333 uds_socket robot_1&
./DDStarter.py

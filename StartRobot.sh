#!/bin/bash
java -jar DataturbineExporter.jar 192.168.1.131:3333 uds_socket dirt&
./DDStarter.py

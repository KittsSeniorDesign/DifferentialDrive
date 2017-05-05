#!/bin/bash
cd DataturbineExporter
make clean
make -j2 
cp build/DataturbineExporter.jar ../
cd ../


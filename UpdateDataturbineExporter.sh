#!/bin/bash
cd DataturbineExporter
make clean
make -j2 JAR=/usr/lib/jvm/java-8-openjdk/bin/jar
cp build/DataturbineExporter.jar ../
cd ../


#!/bin/bash

cd ../

pip install pyserial

git clone https://github.com/pozyxLabs/Pozyx-Python-library.git && cd Pozyx-Python-library
python setup.py install
cd ../

git clone Pillager225@gitlab.com:DecaBot/JUDS.git && cd JUDS
./autoconf.sh && JAVA_HOME=/usr/lib/jvm/java-8-openjdk ./configure
make -j2 && mv juds-*.jar juds.jar
cd ../

git clone https://Pillager225@gitlab.com/DecaBot/DataturbineExporter.git
cp JUDS/juds.jar DataturbineExporter
cd DataturbineExporter
make -j2 JAR=/usr/lib/jvm/java-8-openjdk/bin/jar 
cd ../

cp DataturbineExporter/build/DataturbineExporter.jar DifferentialDrive/
cp JUDS/juds.jar DifferentialDrive/


#!/bin/bash
git clone https://gitlab.com/DecaBot/JUDS.git
cd JUDS
./autoconf.sh
JAVA_HOME=/usr/lib/jvm/java-8-openjdk ./configure
make
make install
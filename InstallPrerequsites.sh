cd ../
git clone https://Pillager225@gitlab.com/DecaBot/JUDS.git
cd JUDS
./autoconf.sh
JAVA_HOME=/usr/lib/jvm/java-8-openjdk ./configure
make
cd ../
git clone https://github.com/pozyxLabs/Pozyx-Python-library.git
cd Pozyx-Python-library/
sudo python setup.py install
cd ../
sudo pip install pyserial
cd DifferentialDrive
./UpdateDataturbineExporter.sh

JUDS has to be compiled by hand as it uses a native C library.

```
git clone git@gitlab.com:DecaBot/JUDS.git && cd JUDS
./autoconf.sh && JAVA_HOME=/usr/lib/jvm/java-8-openjdk ./configure
make -j2 && mv juds-*.jar juds.jar
```
put both `juds.jar` and `rbnb.jar` in the top level directory (with the
makefile). For some reason the edison does not have `jar` linked into the path
by default so either do
```
ln -s /usr/lib/jvm/java-8-openjdk/bin/jar /usr/bin/jar
```
And run `make` as usual, or just tell make where `jar` is, like
```
make JAR=/usr/lib/jvm/java-8-openjdk/bin/jar
```

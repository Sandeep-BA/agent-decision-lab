#!/usr/bin/env sh
# Author: Sandeep Belgavi. Compiles the counting resolver provider and runs the cache scenarios (JDK 18+).
# Arguments: scenario seconds [cache.ttl] [cache.negative.ttl] [cache.stale.ttl] [resolver-fails-at-second]; "-" keeps the default.
set -eu
cd "$(dirname "$0")"
rm -rf out && mkdir out
javac -d out src/*.java
cp -r src/META-INF out/
java -cp out DnsCacheProbe default 65
java -cp out DnsCacheProbe ttl5 21 5
java -cp out DnsCacheProbe ttl0 6 0
java -cp out DnsCacheProbe negative 25
java -cp out DnsCacheProbe nostale 12 3 - - 5
java -cp out DnsCacheProbe stale 30 3 - 10 5
java -cp out DnsCacheProbe late 6

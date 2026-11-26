#!/usr/bin/env sh
# Author: Sandeep Belgavi. Runs the three probes with the JDK on PATH (single-file source launch, JDK 11+).
set -eu
cd "$(dirname "$0")"
java RecursiveUpdate.java
java FibSweep.java
java Frames.java

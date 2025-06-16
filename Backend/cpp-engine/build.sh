#!/bin/bash
cd "$(dirname "$0")"
mkdir -p build
cd build
cmake .. > /dev/null
make -j$(nproc) > /dev/null
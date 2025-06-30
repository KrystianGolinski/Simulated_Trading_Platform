#!/bin/bash
cd "$(dirname "$0")"
mkdir -p build
cd build

# Log build output to file for debugging
LOG_FILE="build.log"
echo "Building C++ engine at $(date)" > "$LOG_FILE"

cmake .. 2>&1 | tee -a "$LOG_FILE"
CMAKE_EXIT_CODE=${PIPESTATUS[0]}

if [ $CMAKE_EXIT_CODE -ne 0 ]; then
    echo "CMAKE FAILED - check $LOG_FILE for details"
    exit $CMAKE_EXIT_CODE
fi

make -j$(nproc) 2>&1 | tee -a "$LOG_FILE"
MAKE_EXIT_CODE=${PIPESTATUS[0]}

if [ $MAKE_EXIT_CODE -ne 0 ]; then
    echo "MAKE FAILED - check $LOG_FILE for details"
    exit $MAKE_EXIT_CODE
fi

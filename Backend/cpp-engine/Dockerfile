# Multi-platform base image
FROM ubuntu:22.04

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpq-dev \
    nlohmann-json3-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy source files
COPY CMakeLists.txt .
COPY build.sh .
COPY src/ src/
COPY include/ include/
COPY tests/ tests/

# Make build script executable and build
RUN chmod +x build.sh && ./build.sh

# Build completes - tests will be run after services are up

# Health check for the C++ engine
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD test -x /shared/trading_engine || exit 1

# Keep container running for volume sharing
CMD ["tail", "-f", "/dev/null"]
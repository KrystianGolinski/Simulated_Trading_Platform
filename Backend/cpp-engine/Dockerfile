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

# Run tests to verify build
RUN ./build/test_basic

# Default command
CMD ["./build/trading_engine", "--help"]
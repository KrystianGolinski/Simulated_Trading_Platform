# Multi-stage Docker build for C++ Engine

# Stage 1: Build stage
FROM ubuntu:22.04 AS builder

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
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
COPY src/ src/
COPY include/ include/
COPY tests/ tests/

# Configure and build the project
RUN mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc)

# Stage 2: Runtime stage
FROM ubuntu:22.04 AS runtime

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy built executables from builder stage
COPY --from=builder /app/build/trading_engine /app/trading_engine
COPY --from=builder /app/build/test_comprehensive /app/test_comprehensive

# Health check for the C++ engine using status command
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/trading_engine --status || exit 1

# Run the trading engine
CMD ["/app/trading_engine"]
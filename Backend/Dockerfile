# Multi-stage Docker build for C++ Backend (Two Executables)

# Stage 1: Build stage
FROM ubuntu:22.04 AS builder

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libpq-dev \
    nlohmann-json3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy all source files
COPY cpp-common/ cpp-common/
COPY trading-engine/ trading-engine/
COPY simulation-orchestrator/ simulation-orchestrator/

# Build trading-engine (worker) - existing functionality
RUN mkdir -p trading-engine/build && cd trading-engine/build && \
    cmake .. && \
    make -j$(nproc)

# Build cpp-common (shared library)
RUN mkdir -p cpp-common/build && cd cpp-common/build && \
    cmake .. && \
    make -j$(nproc)

# Build simulation-orchestrator (manager)
RUN mkdir -p simulation-orchestrator/build && cd simulation-orchestrator/build && \
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
COPY --from=builder /app/trading-engine/build/trading_engine /app/trading_engine
COPY --from=builder /app/trading-engine/build/test_comprehensive /app/test_comprehensive
COPY --from=builder /app/simulation-orchestrator/build/simulation-orchestrator /app/simulation-orchestrator

# Health check for the backend using orchestrator status
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/trading_engine --status || exit 1

# Default command (can be overridden)
CMD ["/app/simulation-orchestrator"]
# Custom TimescaleDB image with Python3 for database initialization scripts
FROM timescale/timescaledb:latest-pg15

# Install Python3 and pip (Alpine Linux uses apk)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    gcc \
    musl-dev

# Set working directory for initialization scripts
WORKDIR /docker-entrypoint-initdb.d

# Copy Python requirements and create virtual environment during build
COPY requirements.txt ./
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Make sure the virtual environment is available in PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy all initialization files
COPY . .

# Fix file permissions and ownership
RUN chmod +x *.sh *.py && \
    chown -R postgres:postgres /docker-entrypoint-initdb.d && \
    chmod -R 755 /docker-entrypoint-initdb.d

# Use the original postgres entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]
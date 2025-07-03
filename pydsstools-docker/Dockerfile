FROM --platform=linux/amd64 python:3.10-slim

# Install system build dependencies (required for pydsstools compilation)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    zlib1g-dev \
    gfortran \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create directories for pydsstools
RUN mkdir -p /pydsstools/src/external/dss/linux64 \
    && mkdir -p /pydsstools/src/external/gridv6/headers \
    && mkdir -p /pydsstools/src/external/zlib

# Copy heclib.a from the local directory
COPY heclib/heclib.a /pydsstools/src/external/dss/linux64/

# Set environment variables for compilation
ENV CFLAGS="-I/usr/include -I/pydsstools/src/external/dss/headers -I/pydsstools/src/external/gridv6/headers"
ENV LDFLAGS="-L/usr/lib/x86_64-linux-gnu -L/pydsstools/src/external/dss/linux64"

# Install Python dependencies (updated July 2025)
RUN pip install --no-cache-dir \
    numpy==1.24.4 \
    pandas==2.0.3 \
    PyYAML==6.0.1 \
    psutil==5.9.8 \
    setuptools \
    wheel

# Install pydsstools
RUN pip install --no-cache-dir pydsstools

# Set the default command
CMD ["python"]
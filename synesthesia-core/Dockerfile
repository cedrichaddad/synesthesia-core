# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Maturin
RUN pip install maturin

# Copy source code
COPY . .

# Build the wheel
RUN maturin build --release --out dist

# Stage 2: Final
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
# ffmpeg is required for pydub
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the wheel from builder
COPY --from=builder /app/dist/*.whl /tmp/

# Install the wheel and dependencies
RUN pip install /tmp/*.whl

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "synesthesia.api:app", "--host", "0.0.0.0", "--port", "8000"]

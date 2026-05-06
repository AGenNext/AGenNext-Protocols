FROM python:3.11-slim

LABEL maintainer="AGenNext"
LABEL description="AGenNext Protocols - AI Agent Protocols SDK"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port for examples
EXPOSE 8000

# Default command
CMD ["python", "-c", "import agennext; print('AGenNext Protocols v' + agennext.__version__)"]

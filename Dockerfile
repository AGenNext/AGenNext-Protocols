FROM python:3.11-slim

LABEL maintainer="AGenNext"
LABEL description="AGenNext Protocols - AI Agent Protocols SDK"

# Set working directory
WORKDIR /app

# Install pip first
RUN pip install --no-cache-dir pip

# Copy project files
COPY pyproject.toml .
COPY agennext ./agennext

# Install dependencies
RUN pip install --no-cache-dir \
    httpx>=0.27.0 \
    pydantic>=2.0.0 \
    python-dotenv>=1.0.0 \
    sseclient>=3.0.0 \
    pyjwt>=2.0.0

# Install package
RUN pip install --no-cache-dir .

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-c", "import agennext; print('AGenNext Protocols v' + agennext.__version__)"]

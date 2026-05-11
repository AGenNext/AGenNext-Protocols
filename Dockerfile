FROM python:3.11-slim

LABEL maintainer="AGenNext"
LABEL description="AGenNext Protocols - AI Agent Protocols SDK"

WORKDIR /app

RUN pip install --no-cache-dir --break-system-packages pip

COPY pyproject.toml .
COPY agennext ./agennext

RUN pip install --no-cache-dir --break-system-packages \
    httpx>=0.27.0 \
    pydantic>=2.0.0 \
    python-dotenv>=1.0.0 \
    sseclient>=3.0.0 \
    pyjwt>=2.0.0

RUN pip install --no-cache-dir --break-system-packages .

EXPOSE 8000

CMD ["python", "-c", "import agennext; print('AGenNext Protocols v' + agennext.__version__)"]

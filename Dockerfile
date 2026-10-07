FROM python:3.9.25-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    OLLAMA_BASE_URL=http://host.docker.internal:11434

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .

RUN echo "=== REQUIREMENTS ===" && cat requirements.txt

RUN python -m pip install --no-cache-dir -r requirements.txt

# Build should stop here if Streamlit wasn't installed
RUN python -m pip show streamlit && \
    python -c "import streamlit; print('Streamlit version:', streamlit.__version__)"

COPY . .

EXPOSE 8501

ENTRYPOINT ["python", "-m", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
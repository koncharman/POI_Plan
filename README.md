# POI_Plan
Plan a trip in Corfu based on a list of POIs and user textual instructions. 

The project uses:

Entity extraction: Standard NLP techniques in combination with LLM assistance using prompts

Vector databases (ChromaDB): Store information about POIs names and tags

RAG: Retrieve relevant documents and tags based on user inputs

Weather API: Adjust plans according to raining conditions

Planning system: Create plans based on user preferences, 
accounting for opening hours, user mentions of POIs or subjects, 
total trip duration and desired trip hours

# Technologies
Streamlit for Application

ChromaDB for vector databases

LangChain for embeddings and LLM integration

OLLAMA models

# Python
Python 3.9.9

Docker Version runs on python:3.9.25-slim-bookworm

# Install Requirements
```bash
pip install -r requirements.txt
```

# OLLAMA
You need to download ollama to run the application.
Two models were used:
```bash
ollama pull llama3.2:3b 
ollama pull nomic-embed-text
```

# Application
After installing the above requirements, you can run the streamlit application.
```bash
streamlit run main.py
```

# Docker

For the docker version, the Docker Desktop must be installed and running.

Ollama runs on the host machine, while the Streamlit application runs inside Docker.

Make sure Ollama is accessible from Docker.

On Windows, set the following environment variable:

```bash
OLLAMA_HOST=0.0.0.0:11434
```

Restart Ollama after setting the variable.

Verify that Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

Build the Docker image from the project directory:

```bash
docker build -t poiplan .
```

Run the application:

```bash
docker run --rm -p 8501:8501 poiplan
```

The application will be available at:

```text
http://localhost:8501
```

Inside Docker, the application connects to Ollama using:

```text
http://host.docker.internal:11434
```

The Docker image sets:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

The Python application should read this value instead of using a hardcoded Ollama URL.

Example:

```python
import os

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)
```

To verify that Docker can communicate with Ollama:

```bash
docker run --rm --entrypoint curl poiplan http://host.docker.internal:11434/api/tags
```




# Flow
```mermaid
flowchart TD
    POI["POI Data<br>(Name; Area; Tags; Category; Family Friendly; Visit Time; Indoor/Outdoor/Mixed)"]
    POI --> VS["Vector Stores"]

    IN["User Input"]
    IN --> EE["Entity Extraction"]

    EE --> DT["Date, Weekday, Duration, No Stops, and Time Extraction"]
    EE --> RAG["RAG based on POIs Names and Tags"]
    VS --> RAG

    RAG --> FT_DR["Requested POIs"]
    RAG --> FT_RR["Account for raining (if requested)"]
    RAG --> FT_FF["Account for family friendly POIs (if requested)"]
    RAG --> FT_IO["Account for indoor or outdoor settings (if requested)"]

    FT_DR --> FP["Filtered POIs"]
    FT_RR --> FP
    FT_FF --> FP
    FT_IO --> FP

    FP --> CP["Plan Creation"]
    DT --> CP

    CP --> UO["User Output (List of Plans)"]
```

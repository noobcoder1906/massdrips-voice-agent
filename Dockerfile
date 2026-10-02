FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg git curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chatterbox and its exact dependencies without breaking PyTorch
RUN pip install --no-cache-dir chatterbox-tts --no-deps
RUN pip install --no-cache-dir resemble-perth s3tokenizer conformer omegaconf pyloudnorm pykakasi --no-deps

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

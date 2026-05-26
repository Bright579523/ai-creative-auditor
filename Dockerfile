# Base image
FROM python:3.10

WORKDIR /code

# Install system libraries required by OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Copy application files
COPY --chown=user . $HOME/app

# Pre-download EasyOCR models (en, th) and pre-load YOLOv8 so they are cached in the image
RUN python -c "import easyocr; easyocr.Reader(['en', 'th'])"
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Run Streamlit (all config in .streamlit/config.toml)
CMD ["streamlit", "run", "app.py"]
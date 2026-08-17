FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# CPU-only torch first: sentence-transformers pulls in torch unpinned, and the
# default PyPI wheel bundles ~2GB of NVIDIA CUDA packages this container never
# uses (no GPU here). Installing the CPU wheel first satisfies that dependency
# without pip ever reaching for the CUDA build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "run.py"]

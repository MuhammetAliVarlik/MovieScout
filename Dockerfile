FROM python:3.11-slim

WORKDIR /app

# Unbuffered stdout/stderr so `docker logs` shows progress and errors as they
# happen, instead of sitting silent until an internal buffer flushes.
ENV PYTHONUNBUFFERED=1
# Bake the HF cache under /app (owned by appuser below) instead of the
# default ~/.cache — /root wouldn't be readable once we drop root.
ENV HF_HOME=/app/.cache/huggingface

COPY requirements.txt .
# CPU-only torch first: sentence-transformers pulls in torch unpinned, and the
# default PyPI wheel bundles ~2GB of NVIDIA CUDA packages this container never
# uses (no GPU here). Installing the CPU wheel first satisfies that dependency
# without pip ever reaching for the CUDA build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image at build time so every container
# start doesn't re-download it from Hugging Face (slow, and looks like a
# hang since nothing prints while it's happening).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# Run as a non-root user — nothing here needs root once deps are installed.
# No chown needed: everything under /app was written by root with the
# default umask (world-readable), which is all a read-only interpreter needs;
# the only things the app writes at runtime (data/chroma, data/flask_session,
# data/processed) live under the bind-mounted ./data volume, whose ownership
# comes from the host, not this image. UID 1000 matches the default first-user
# account on most Linux hosts, so that bind mount stays writable on a typical
# setup; if you hit permission errors on yours, `chmod -R a+rwX ./data` on
# the host is the quick fix.
RUN useradd --uid 1000 --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 5000
CMD ["python", "run.py"]

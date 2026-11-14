FROM python:3.11-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip ca-certificates git poppler-utils && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt
COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY skills/ /workspace/skills/
# Source-data bootstrap intentionally disabled: only released visible data may enter the image.
COPY ACCESS_POLICY.md /workspace/ACCESS_POLICY.md
CMD ["bash"]

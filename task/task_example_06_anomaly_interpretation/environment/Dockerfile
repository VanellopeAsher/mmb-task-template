FROM python:3.11-slim AS data_builder
WORKDIR /workspace
RUN pip install --no-cache-dir requests==2.32.3 ase==3.24.0
COPY data/fetch_data.py /workspace/data/fetch_data.py
RUN python /workspace/data/fetch_data.py

FROM python:3.11-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip ca-certificates git poppler-utils && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt
COPY data/README.md /workspace/data/README.md
COPY --from=data_builder /workspace/data/structures/ /workspace/data/structures/
COPY tools/ /workspace/tools/
COPY skills/ /workspace/skills/
CMD ["bash"]

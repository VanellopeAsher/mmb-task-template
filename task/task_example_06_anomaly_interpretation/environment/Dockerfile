FROM python:3.11.11-slim-bookworm@sha256:081075da77b2b55c23c088251026fb69a7b2bf92471e491ff5fd75c192fd38e5
WORKDIR /workspace
COPY requirements.txt requirements.lock /workspace/
RUN pip install --no-cache-dir --require-hashes -r /workspace/requirements.lock
COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY skills/ /workspace/skills/
CMD ["bash"]

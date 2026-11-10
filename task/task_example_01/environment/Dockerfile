# Agent-visible scientific environment. A production release should replace
# the base tag with a tested image digest and lock transitive package hashes.
FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /workspace/requirements.txt
RUN python -m pip install --no-cache-dir -r /workspace/requirements.txt

COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY skills/ /workspace/skills/

CMD ["bash"]

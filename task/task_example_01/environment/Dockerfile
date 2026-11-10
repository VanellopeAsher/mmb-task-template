# Agent-visible scientific environment. Base image digest was tested in CI.
FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /workspace/requirements.lock
RUN python -m pip install --no-cache-dir -r /workspace/requirements.lock \
    && python -m pip check

COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY skills/ /workspace/skills/

CMD ["bash"]

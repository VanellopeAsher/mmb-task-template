# Agent's reproducible scientific environment. Pin the base image by digest and
# install only the software required by this task before accepting a live task.
FROM python:3.11-slim

WORKDIR /workspace

# Add pinned packages and task tools here. Copy only agent-visible inputs;
# never copy feasibility/, tests/, or authoring/ into this image.
COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY skills/ /workspace/skills/

CMD ["bash"]

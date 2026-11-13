FROM python:3.11-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip ca-certificates git poppler-utils && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt
RUN python -c "from larch.xafs import pre_edge, autobk, xftf, feffit; from pymcr.mcr import McrAR"
COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY skills/ /workspace/skills/
RUN if [ -f /workspace/data/fetch_data.sh ]; then bash /workspace/data/fetch_data.sh; fi
CMD ["bash"]

# Agent-visible scientific environment.
FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

WORKDIR /workspace
RUN mkdir -p /workspace/results

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libeigen3-dev \
       gfortran libopenmpi-dev openmpi-bin libsymspg-dev liblapack-dev \
       libblas-dev git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git init /opt/fourphonon \
    && git -C /opt/fourphonon remote add origin https://github.com/FourPhonon/FourPhonon.git \
    && git -C /opt/fourphonon fetch --depth 1 origin 5b814b337e03e72907a15a2c953723171fba7102 \
    && git -C /opt/fourphonon checkout --detach FETCH_HEAD
COPY fourphonon.patch /opt/fourphonon.patch
RUN git -C /opt/fourphonon apply /opt/fourphonon.patch \
    && make -C /opt/fourphonon/Src cpu -j1 \
    && ln -s /opt/fourphonon/ShengBTE_cpu /usr/local/bin/fourphonon-shengbte

COPY requirements.txt /workspace/requirements.txt
RUN python -m pip install --no-cache-dir -r /workspace/requirements.txt \
    && python -m pip check

COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
RUN python /workspace/tools/check_software.py

CMD ["bash"]

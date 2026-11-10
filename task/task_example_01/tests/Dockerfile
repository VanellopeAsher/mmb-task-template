# Separate, network-free verifier with only the objective checks.
FROM python:3.11-slim

WORKDIR /tests
COPY . /tests/
RUN mkdir -p /workspace/results /logs/verifier

CMD ["bash", "/tests/test.sh"]

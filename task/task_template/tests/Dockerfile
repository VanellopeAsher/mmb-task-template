# Isolated verifier environment. Pin the image by digest and install only
# dependencies needed for objective checks. Keep hidden evidence out of the
# agent image; mount it only into the verifier where required.
FROM python:3.11-slim

WORKDIR /tests
COPY test.sh /tests/test.sh

CMD ["bash", "/tests/test.sh"]

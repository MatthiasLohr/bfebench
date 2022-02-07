
FROM python:3.9 AS builder
COPY ./dist/*.tar.gz /tmp/bfebench.tar.gz
ENV PATH="/opt/bfebench/bin:$PATH"
RUN python -m venv /opt/bfebench \
    && pip install --no-cache-dir /tmp/bfebench.tar.gz

FROM python:3.9-slim
ENV PATH="/opt/bfebench/bin:$PATH"
COPY --from=builder /opt/bfebench /opt/bfebench
COPY ./tools/generate-test-data.py /opt/bfebench/bin/generate-test-data.py
COPY ./blockchain-networks/ganache/bfebench-environments.yaml /opt/bfebench/ganache.environments.yaml
ENTRYPOINT ["/opt/bfebench/bin/bfebench"]

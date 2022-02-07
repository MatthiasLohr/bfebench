
FROM python:3.9
ADD . /opt/bfebench
WORKDIR /opt/bfebench
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_BFEBENCH "0.1.0"
RUN pip install -e .

FROM python:3.11-slim-trixie@sha256:bab1b7ef4b450c81002278d035eff85ebe394ae94df904f7a3ba14f7e16e487b

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_CONFIG=production \
    FLASK_DEBUG=0

RUN apt-get update && \
    apt-get upgrade --yes --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.lock /app/requirements.lock
RUN pip install --require-hashes -r /app/requirements.lock

# Build tooling is not needed by the runtime application. Removing it also
# removes setuptools' vendored copies of packages from the final image.
RUN python -m pip uninstall --yes wheel setuptools && \
    python -m pip uninstall --yes pip

COPY . /app

RUN mkdir -p /home/appuser && \
    printf 'appuser:x:10001:10001:appuser:/home/appuser:/usr/sbin/nologin\n' >> /etc/passwd && \
    printf 'appuser:x:10001:\n' >> /etc/group && \
    chown -R 10001:10001 /app /home/appuser
ENV HOME=/home/appuser
USER 10001:10001

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "wsgi:app"]

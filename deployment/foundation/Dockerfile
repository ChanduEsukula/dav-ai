FROM python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741 AS dependencies
WORKDIR /build
COPY deployment/foundation/requirements.lock /build/requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /build/requirements.lock

FROM python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741
ENV PATH=/opt/venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DAVAI_ENV=staging DAVAI_FOUNDATION_MODE=deny PORT=8080
WORKDIR /foundation
COPY --from=dependencies /opt/venv /opt/venv
COPY deployment/foundation/app.py /foundation/app.py
# Package installers and their vendored libraries are not needed in the runtime.
RUN /opt/venv/bin/python -m pip uninstall --yes pip && /usr/local/bin/python -m pip uninstall --yes pip
USER 65532:65532
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ['PORT']+'/health',timeout=2)"]
CMD ["python", "/foundation/app.py"]

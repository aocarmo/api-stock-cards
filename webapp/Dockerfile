# Build a partir da RAIZ do repo (context: ..), pois a app reusa `enums/`.
#   docker build -f webapp/Dockerfile -t myp-webapp ..
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8001

WORKDIR /app/webapp

COPY webapp/requirements.txt ./
RUN pip install -r requirements.txt

# enums/ fica em /app/enums; config.py adiciona /app ao sys.path
COPY enums/ /app/enums/
COPY webapp/ /app/webapp/

EXPOSE 8001
CMD ["python", "run.py"]

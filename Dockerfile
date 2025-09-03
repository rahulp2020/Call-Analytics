FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip

RUN echo "Installing fast packages..." && \
    pip install --only-binary=:all: aiofiles==24.1.0 async-timeout==5.0.1 attrs==25.3.0 redis==5.2.1 PyJWT==2.8.0

RUN echo "Installing web frameworks..." && \
    pip install --only-binary=:all: aiohttp==3.12.15 fastapi==0.116.1 pydantic==2.11.7 uvicorn==0.35.0 sqlalchemy==2.0.43

RUN echo "Installing celery and openai..." && \
    pip install --only-binary=:all: celery==5.5.3 openai==1.102.0

RUN echo "Installing huggingface hub..." && \
    pip install --only-binary=:all: huggingface-hub==0.34.4

RUN echo "Installing numpy..." && \
    pip install --only-binary=:all: numpy==2.0.2

# Heavy ML - Transformers (5-15 minutes)
RUN echo "Installing transformers (this will take several minutes)..." && \
    pip install --only-binary=:all: transformers==4.56.0

RUN echo "Installing sentence-transformers (final heavy package)..." && \
    pip install --only-binary=:all: sentence-transformers==5.1.0

COPY . .

EXPOSE 8000

CMD ["uvicorn", "Apis.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
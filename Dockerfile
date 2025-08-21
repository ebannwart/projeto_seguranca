FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

ENV PORT=8000

EXPOSE $PORT

CMD gunicorn app:app --bind 0.0.0.0:$PORT
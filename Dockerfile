FROM python:3.11-slim-buster

ENV SECRET_KEY="your_secret_key_value"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pkg-config \
    build-essential \
    gcc \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY requirements.txt requirements.txt
COPY manage.py manage.py
COPY Manager Manager
COPY App App

RUN pip install --no-cache -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

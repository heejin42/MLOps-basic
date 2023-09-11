FROM amd64/python:3.9-slim

WORKDIR /usr/app

RUN pip install -U pip && pip install psycopg2-binary kafka-python requests

COPY 8_data_subscriber.py 8_data_subscriber.py

ENTRYPOINT [ "python", "8_data_subscriber.py" ]
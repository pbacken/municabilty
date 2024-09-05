FROM python:slim

RUN pip install gunicorn pymysql cryptography
RUN apt update -y
RUN apt install portaudio19-dev gcc -y
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


COPY app app
COPY migrations migrations
COPY sunfish.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP sunfish.py
RUN flask

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]

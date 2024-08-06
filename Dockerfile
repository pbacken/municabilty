FROM python:slim

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn pymysql cryptography
RUN apt install portaudio19-dev

COPY app app
COPY migrations migrations
COPY sunfish.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP sunfish.py
RUN flask

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]

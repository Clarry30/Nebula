FROM python:3.11

WORKDIR /usr/bin/flask

COPY requirements.txt /usr/bin/flask/

RUN pip install -r requirements.txt

EXPOSE 5000

CMD [ "python", "./usr/bin/flask/nebbackend.py"]

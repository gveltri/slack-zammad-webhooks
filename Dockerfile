FROM tiangolo/uwsgi-nginx-flask:python2.7

COPY ./app /app

RUN pip install -r ./requirements.txt


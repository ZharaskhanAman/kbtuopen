ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/
COPY . /code

RUN mkdir /var/log/gunicorn
RUN touch /var/log/gunicorn/access.log
RUN touch /var/log/gunicorn/error.log

EXPOSE 8000

CMD ["/bin/bash", "-c", "python manage.py collectstatic --noinput; python manage.py migrate; gunicorn --bind :8000 --workers 2 --error-logfile /var/log/gunicorn/error.log --access-logfile /var/log/gunicorn/access.log kbtuopen.wsgi"]

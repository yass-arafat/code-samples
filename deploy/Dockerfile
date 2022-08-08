FROM python:3.7.9-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cleaning up unused files
  # && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/production.txt \
    && rm -rf /requirements

# COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
# RUN sed -i 's/\r$//g' /entrypoint
# RUN chmod +x /entrypoint


# COPY --chown=django:django ./compose/production/django/start /start
# RUN sed -i 's/\r$//g' /start
# RUN chmod +x /start
# COPY --chown=django:django . /app

# USER django

WORKDIR /app

COPY . /app

# RUN /usr/local/bin/python manage.py collectstatic --noinput

RUN mkdir logs; touch logs/ErrorLoggers.log; touch logs/InfoLoggers.log; mkdir -p /app/core/static

CMD ["/usr/local/bin/gunicorn" ,"config.wsgi" ,"--bind" ,"0.0.0.0:5000" ,"--chdir=/app"]

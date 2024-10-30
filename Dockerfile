# Define Python version as an argument
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y cron sqlite3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Berlin

# Show the currently running commands
SHELL ["sh", "-exc"]

# Set working directory
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir
COPY . /app
# See <https://hynek.me/articles/docker-signals/>.
STOPSIGNAL SIGINT
# VERY IMPORTANT STEP SINCE THE CRONJOB DOESN'T READ THE ENV_VARS BY DEFAULT
RUN chmod +x /app/bin/entrypoint.sh

# run every 2 minutes from monday to friday (8 am to 21)
RUN echo "*/2 8-21 * * 1-5 cd /app && /usr/local/bin/python3 /app/main.py >> /var/log/cron.log 2>&1" > /tmp/parker \
  && crontab /tmp/parker

ENTRYPOINT ["/app/bin/enable_env.sh"]
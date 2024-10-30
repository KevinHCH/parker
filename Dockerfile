# Define Python version as an argument
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y cron sqlite3
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
ENV FLARESOLVER_ENDPOINT=value
ENV NOTIFICATION_ENDPOINT=value
# run every 2 minutes from monday to friday (8 am to 21)
RUN echo "*/2 8-21 * * 1-5 cd /app && /usr/local/bin/python3 /app/main.py >> /var/log/cron.log 2>&1" > /tmp/parker \
  && crontab /tmp/parker

# Start cron in the foreground to keep the container running
CMD ["cron", "-f"]
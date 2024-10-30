FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
# Copy the application into the container.
COPY . /app

# Install the application dependencies.
RUN uv sync --frozen --no-cache

RUN useradd -m nonroot && chown -R nonroot:nonroot /app
USER nonroot

# Add cron job for running the script every 2 minutes
RUN echo "*/2 * * * * /app/.venv/bin/python /app/main.py >> /var/logs/cron.log 2>&1" > /tmp/parker \
  && crontab /tmp/parker

VOLUME ["/app/jobs.db"]

# Start cron in the foreground to keep the container running
CMD ["cron", "-f"]
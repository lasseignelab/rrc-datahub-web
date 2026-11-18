"""
Gunicorn settings for production (`gunicorn app:server` loads this file
automatically from the project root).

A data-chat answer can keep a request busy for several seconds while the
model queries the database, and gunicorn's default of one single-threaded
worker would make every other visitor wait for it. Several worker processes,
each with a few threads, let page loads, chart callbacks and other users'
questions run at the same time.

Each setting can be overridden with an environment variable, so a host can
tune them without a code change.
"""

import os

# Worker processes. WEB_CONCURRENCY is the conventional variable that
# hosting platforms set to match the machine's CPU count.
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))

# Threads per worker. Chat requests spend most of their time waiting on the
# OpenAI API and the database, so threads add concurrency cheaply.
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_class = "gthread"

# Seconds a worker may go silent before it is restarted. A chat answer can
# take several tool rounds, so allow well over gunicorn's default of 30.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))

# The app is not preloaded: each worker imports it and opens its own
# database connections after forking, rather than sharing sockets that were
# opened in the parent process.
preload_app = False

# The listen address is left to gunicorn: 127.0.0.1:8000 by default, or
# 0.0.0.0:$PORT when the host sets PORT; `-b` on the command line overrides.

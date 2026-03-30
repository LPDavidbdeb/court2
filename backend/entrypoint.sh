#!/bin/sh

# Stop execution if any command fails
set -e

echo "Applying database migrations..."
python manage.py migrate


echo "Starting Gunicorn..."
exec "$@"

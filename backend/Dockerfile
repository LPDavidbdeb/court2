# Dockerfile

# Use the same Python version as your local environment
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    zlib1g-dev \
    # Add any other system dependencies your Court project might need, e.g., gdal-bin, libgdal-dev if using GeoDjango
    && rm -rf /var/lib/apt/lists/*

# Copy your production requirements.txt file
COPY requirements.txt .

# Install dependencies directly
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# NEW: Set the environment to 'remote' BEFORE running collectstatic
# This tells Django to load remote.py (using psycopg2)
# instead of local.py (using mysqlclient).
ENV DJANGO_ENV=remote

# --- THIS LINE IS NOW COMMENTED OUT AS PER YOUR INSTRUCTIONS ---
# RUN python manage.py collectstatic --noinput
RUN SECRET_KEY=build_dummy_key \
    DB_ENGINE=django.db.backends.postgresql \
    GS_BUCKET_NAME=build_dummy_bucket \
    GOOGLE_CLOUD_PROJECT=build_dummy_project \
    python manage.py collectstatic --noinput
# Set environment variables for Cloud Run
ENV PORT=8080

# --- NEW ENTRYPOINT LOGIC ---
# Copy the entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

# Make it executable (Important!)
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# The CMD passes arguments to the ENTRYPOINT (starts Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "mysite.wsgi:application"]

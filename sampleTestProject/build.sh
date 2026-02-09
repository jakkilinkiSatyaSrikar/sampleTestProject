#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install libraries
pip install -r requirements.txt

# Run Django commands
python manage.py collectstatic --no-input
python manage.py migrate